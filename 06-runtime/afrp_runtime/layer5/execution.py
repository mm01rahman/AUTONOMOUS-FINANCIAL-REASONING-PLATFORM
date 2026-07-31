"""L5-EXE — order gateway and portfolio reconciliation (SLS-500).

The gateway owns the exhaustive order state machine (CIO-08), consumes venue
events (CIO-09), and the reconciler emits portfolio snapshots (CIO-10).
Every state change is synchronously written through an abstract event-store
port (EDR-001) and HMAC-signed with trace context (NFR-005/NFR-007).
"""

from __future__ import annotations

import hmac
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Protocol

from afrp_runtime.common.errors import ConfigurationError, ContractViolationError
from afrp_runtime.contracts.cio import (
    AuthorizationVerdict,
    AuthorizedAction,
    ExecutionEventKind,
    ExecutionIntent,
    ExecutionReport,
    OrderState,
    PortfolioState,
    Position,
)
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L5-EXE"
_AUDIT_KEY_ENV = "AFRP_AUDIT_HMAC_KEY"
_EPSILON = 1e-9


class OrderEventStore(Protocol):
    """Durable append port implemented by L1-RDB at composition time."""

    def append_order_event(
        self, order_id: str, event: str, quantity: float, price: float, at_ns: int
    ) -> None:
        """Synchronously append one order event (RPO = 0)."""


@dataclass
class InMemoryOrderEventStore:
    """Deterministic event-store fixture and development adapter."""

    events: list[tuple[str, str, float, float, int]] = field(default_factory=list)

    def append_order_event(
        self, order_id: str, event: str, quantity: float, price: float, at_ns: int
    ) -> None:
        self.events.append((order_id, event, quantity, price, at_ns))


@dataclass(frozen=True)
class AuditEntry:
    """Cryptographically authenticated order audit event (NFR-007)."""

    order_id: str
    state: OrderState
    event: str
    at_ns: int
    trace_id: str
    span_id: str
    signature: bytes

    @property
    def payload(self) -> str:
        """Canonical signed representation."""
        return (
            f"{self.order_id}:{int(self.state)}:{self.event}:{self.at_ns}:"
            f"{self.trace_id}:{self.span_id}"
        )


@dataclass
class AuditLedger:
    """Append-only HMAC audit ledger."""

    key: bytes
    entries: list[AuditEntry] = field(default_factory=list)

    @classmethod
    def from_environment(cls) -> AuditLedger:
        """Load the HMAC key from the environment (EDR-008)."""
        raw = os.environ.get(_AUDIT_KEY_ENV, "")
        if not raw:
            raise ConfigurationError(
                _AUDIT_KEY_ENV, "order audit key must be provided via environment"
            )
        return cls(raw.encode("utf-8"))

    def append(
        self,
        order_id: str,
        state: OrderState,
        event: str,
        at_ns: int,
        trace_id: str,
        span_id: str,
    ) -> AuditEntry:
        """Sign and append one audit event."""
        unsigned = f"{order_id}:{int(state)}:{event}:{at_ns}:{trace_id}:{span_id}"
        signature = hmac.new(self.key, unsigned.encode("utf-8"), sha256).digest()
        entry = AuditEntry(
            order_id=order_id,
            state=state,
            event=event,
            at_ns=at_ns,
            trace_id=trace_id,
            span_id=span_id,
            signature=signature,
        )
        self.entries.append(entry)
        return entry

    def verify(self, entry: AuditEntry) -> bool:
        """Verify one entry's HMAC in constant time."""
        expected = hmac.new(self.key, entry.payload.encode("utf-8"), sha256).digest()
        return hmac.compare_digest(entry.signature, expected)


_LEGAL_TRANSITIONS: dict[OrderState, tuple[OrderState, ...]] = {
    OrderState.NEW: (OrderState.SUBMITTED, OrderState.CANCELLED),
    OrderState.SUBMITTED: (
        OrderState.ACKNOWLEDGED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
    ),
    OrderState.ACKNOWLEDGED: (
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
    ),
    OrderState.PARTIALLY_FILLED: (
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.EXPIRED,
    ),
    OrderState.FILLED: (),
    OrderState.CANCELLED: (),
    OrderState.REJECTED: (),
    OrderState.EXPIRED: (),
    OrderState.UNSPECIFIED: (),
}

_REPORT_TARGET = {
    ExecutionEventKind.ACK: OrderState.ACKNOWLEDGED,
    ExecutionEventKind.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
    ExecutionEventKind.FILL: OrderState.FILLED,
    ExecutionEventKind.CANCEL: OrderState.CANCELLED,
    ExecutionEventKind.REJECT: OrderState.REJECTED,
    ExecutionEventKind.EXPIRE: OrderState.EXPIRED,
}


def legal_order_targets(state: OrderState) -> tuple[OrderState, ...]:
    """Legal successors of an order state."""
    return _LEGAL_TRANSITIONS[state]


@dataclass
class OrderRecord:
    """Mutable internal state for one authorized order."""

    action: AuthorizedAction
    order_id: str
    state: OrderState = OrderState.NEW
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0


class OrderGateway:
    """CIO-08/CIO-09 state machine with synchronous persistence and audit."""

    def __init__(
        self,
        mission_profile_id: str,
        event_store: OrderEventStore | None = None,
        audit_ledger: AuditLedger | None = None,
        order_id_factory: Callable[[], str] | None = None,
        cognitive_cycle_id: str = "cycle-0",
    ) -> None:
        self.mission_profile_id = mission_profile_id
        self.cognitive_cycle_id = cognitive_cycle_id
        self.event_store = event_store or InMemoryOrderEventStore()
        self.audit_ledger = audit_ledger or AuditLedger.from_environment()
        self.order_id_factory = order_id_factory or (lambda: str(uuid.uuid4()))
        self._orders: dict[str, OrderRecord] = {}

    def submit(self, action: AuthorizedAction, at_ns: int) -> ExecutionIntent:
        """Commit an authorized CIO-07 as a submitted CIO-08.

        Raises:
            ContractViolationError: action is null/rejected, unsigned, or has
                invalid size/direction.
        """
        if action.verdict not in (
            AuthorizationVerdict.AUTHORIZED,
            AuthorizationVerdict.PROJECTED,
        ):
            raise ContractViolationError("CIO-08", "only authorized actions may submit")
        if action.direction not in (-1.0, 1.0) or action.size <= 0.0:
            raise ContractViolationError("CIO-08", "sized action requires direction +/-1")
        if not action.hmac_signature:
            raise ContractViolationError("CIO-08", "CIO-07 authorization is unsigned")

        order_id = self.order_id_factory()
        if not order_id or order_id in self._orders:
            raise ContractViolationError("CIO-08", f"duplicate/empty order id {order_id!r}")
        record = OrderRecord(action=action, order_id=order_id)
        self._orders[order_id] = record
        self._persist(record, "NEW", 0.0, action.entry_price, at_ns)
        return self._transition(record, OrderState.SUBMITTED, "SUBMITTED", 0.0, at_ns)

    def apply_report(self, report: ExecutionReport) -> ExecutionIntent:
        """Apply CIO-09 and return the new CIO-08 state.

        Fill events are quantity-conserving: PARTIAL_FILL must leave remainder,
        and FILL must complete exactly the authorized quantity.
        """
        record = self._require_order(report.order_id)
        target = _REPORT_TARGET.get(report.event)
        if target is None:
            raise ContractViolationError("CIO-09", f"unsupported event {report.event}")

        fill_event = report.event in (
            ExecutionEventKind.PARTIAL_FILL,
            ExecutionEventKind.FILL,
        )
        if fill_event:
            new_total, new_average = self._validate_fill_quantity(record, report)
            total = record.action.size
            if (
                report.event is ExecutionEventKind.PARTIAL_FILL
                and new_total >= total - _EPSILON
            ):
                raise ContractViolationError(
                    "CIO-09", "PARTIAL_FILL must leave unfilled quantity"
                )
            if (
                report.event is ExecutionEventKind.FILL
                and abs(new_total - total) > _EPSILON
            ):
                raise ContractViolationError(
                    "CIO-09",
                    f"FILL leaves quantity {total - new_total:.12g}",
                )
            record.filled_quantity = new_total
            record.average_fill_price = new_average
        elif abs(report.fill_quantity) > _EPSILON:
            raise ContractViolationError(
                "CIO-09", f"{report.event.name} must carry zero fill quantity"
            )

        return self._transition(
            record,
            target,
            report.event.name,
            report.fill_quantity,
            report.venue_at_ns,
            report.fill_price,
            parent_id=report.envelope.message_id,
        )

    def cancel(self, order_id: str, at_ns: int) -> ExecutionIntent:
        """Cancel a live order."""
        record = self._require_order(order_id)
        return self._transition(record, OrderState.CANCELLED, "CANCELLED", 0.0, at_ns)

    def snapshot(self, order_id: str, at_ns: int) -> ExecutionIntent:
        """Current CIO-08 snapshot for recovery/checkpointing."""
        return self._make_intent(self._require_order(order_id), at_ns)

    def restore_order(
        self,
        intent: ExecutionIntent,
        action: AuthorizedAction,
        filled_quantity: float = 0.0,
        average_fill_price: float = 0.0,
    ) -> None:
        """Restore one durable order checkpoint without replay side effects."""
        if intent.authorized_action_id != action.envelope.message_id:
            raise ContractViolationError("CIO-08", "checkpoint action id mismatch")
        if not 0.0 <= filled_quantity <= intent.quantity:
            raise ContractViolationError("CIO-08", "checkpoint fill quantity out of bounds")
        self._orders[intent.order_id] = OrderRecord(
            action=action,
            order_id=intent.order_id,
            state=intent.state,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price,
        )

    def record(self, order_id: str) -> OrderRecord:
        """Return a live order record."""
        return self._require_order(order_id)

    def _require_order(self, order_id: str) -> OrderRecord:
        try:
            return self._orders[order_id]
        except KeyError as exc:
            raise ContractViolationError("CIO-09", f"unknown order {order_id!r}") from exc

    def _validate_fill_quantity(
        self, record: OrderRecord, report: ExecutionReport
    ) -> tuple[float, float]:
        """Validate a fill and return prospective total/average without mutation."""
        if report.fill_quantity <= 0.0 or report.fill_price <= 0.0:
            raise ContractViolationError("CIO-09", "fill quantity/price must be positive")
        new_total = record.filled_quantity + report.fill_quantity
        if new_total > record.action.size + _EPSILON:
            raise ContractViolationError(
                "CIO-09",
                f"overfill {new_total:.12g} > authorized {record.action.size:.12g}",
            )
        if new_total > 0.0:
            new_average = (
                record.average_fill_price * record.filled_quantity
                + report.fill_price * report.fill_quantity
            ) / new_total
        else:
            new_average = 0.0
        return new_total, new_average

    def _transition(
        self,
        record: OrderRecord,
        target: OrderState,
        event: str,
        quantity: float,
        at_ns: int,
        price: float = 0.0,
        parent_id: str | None = None,
    ) -> ExecutionIntent:
        if target not in _LEGAL_TRANSITIONS[record.state]:
            raise ContractViolationError(
                "CIO-08", f"illegal order transition {record.state.name} -> {target.name}"
            )
        record.state = target
        self._persist(record, event, quantity, price, at_ns)
        return self._make_intent(record, at_ns, parent_id)

    def _persist(
        self,
        record: OrderRecord,
        event: str,
        quantity: float,
        price: float,
        at_ns: int,
    ) -> None:
        self.event_store.append_order_event(
            record.order_id, event, quantity, price, at_ns
        )
        action_env = record.action.envelope
        self.audit_ledger.append(
            record.order_id,
            record.state,
            event,
            at_ns,
            action_env.trace_id,
            action_env.span_id,
        )

    def _make_intent(
        self, record: OrderRecord, at_ns: int, parent_id: str | None = None
    ) -> ExecutionIntent:
        action = record.action
        parents = [action.envelope.message_id]
        if parent_id:
            parents.append(parent_id)
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{record.order_id}:{record.state.name}:{record.filled_quantity}",
            parent_cio_ids=tuple(parents),
            trace_id=action.envelope.trace_id,
            generated_at_ns=at_ns,
        )
        return ExecutionIntent(
            envelope=envelope,
            order_id=record.order_id,
            authorized_action_id=action.envelope.message_id,
            state=record.state,
            instrument=action.instrument,
            direction=action.direction,
            quantity=action.size,
            limit_price=action.entry_price,
        )


@dataclass
class _PositionBook:
    quantity: float
    average_price: float


@dataclass
class PortfolioReconciler:
    """Fill-driven portfolio ledger emitting CIO-10 snapshots."""

    mission_profile_id: str
    initial_cash: float
    cognitive_cycle_id: str = "cycle-0"
    _cash: float = field(init=False)
    _positions: dict[str, _PositionBook] = field(default_factory=dict)
    _parent_reports: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._cash = self.initial_cash

    def apply_fill(self, intent: ExecutionIntent, report: ExecutionReport) -> None:
        """Apply a partial/final fill to cash and position cost basis."""
        if report.order_id != intent.order_id:
            raise ContractViolationError("CIO-10", "intent/report order mismatch")
        if report.event not in (
            ExecutionEventKind.PARTIAL_FILL,
            ExecutionEventKind.FILL,
        ):
            raise ContractViolationError("CIO-10", "only fill events affect portfolio")
        if report.fill_quantity <= 0.0 or report.fill_price <= 0.0:
            raise ContractViolationError("CIO-10", "fill quantity/price must be positive")

        signed_fill = intent.direction * report.fill_quantity
        self._cash -= signed_fill * report.fill_price
        current = self._positions.get(intent.instrument, _PositionBook(0.0, 0.0))
        old_qty = current.quantity
        new_qty = old_qty + signed_fill

        if abs(old_qty) <= _EPSILON or old_qty * signed_fill > 0.0:
            total_abs = abs(old_qty) + abs(signed_fill)
            average = (
                current.average_price * abs(old_qty)
                + report.fill_price * abs(signed_fill)
            ) / total_abs
        elif abs(signed_fill) < abs(old_qty) - _EPSILON:
            average = current.average_price
        elif abs(new_qty) <= _EPSILON:
            average = 0.0
            new_qty = 0.0
        else:
            average = report.fill_price

        self._positions[intent.instrument] = _PositionBook(new_qty, average)
        self._parent_reports.append(report.envelope.message_id)

    def snapshot(self, marks: dict[str, float], at_ns: int) -> PortfolioState:
        """Mark positions and emit a reconciled CIO-10."""
        positions: list[Position] = []
        market_value = 0.0
        gross_exposure = 0.0
        for instrument, book in sorted(self._positions.items()):
            mark = marks.get(instrument)
            if mark is None or mark <= 0.0:
                raise ContractViolationError(
                    "CIO-10", f"missing/invalid mark for {instrument}"
                )
            unrealized = (mark - book.average_price) * book.quantity
            market_value += mark * book.quantity
            gross_exposure += abs(book.quantity)
            positions.append(
                Position(
                    instrument=instrument,
                    quantity=book.quantity,
                    average_price=book.average_price,
                    unrealized_pnl=unrealized,
                )
            )

        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{self._cash}:{[(p.instrument, p.quantity) for p in positions]}",
            parent_cio_ids=tuple(self._parent_reports),
            generated_at_ns=at_ns,
        )
        return PortfolioState(
            envelope=envelope,
            positions=tuple(positions),
            cash=self._cash,
            equity=self._cash + market_value,
            gross_exposure=gross_exposure,
            reconciled_at_ns=at_ns,
        )

    def restore(self, state: PortfolioState) -> None:
        """Restore a durable CIO-10 checkpoint (RTO recovery path)."""
        self._cash = state.cash
        self._positions = {
            position.instrument: _PositionBook(
                position.quantity, position.average_price
            )
            for position in state.positions
        }
        self._parent_reports = [state.envelope.message_id]
