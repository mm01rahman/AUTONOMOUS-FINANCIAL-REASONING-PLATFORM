"""Unit/integration tests for Layer 5 order FSM, audit, fills, and recovery."""

from __future__ import annotations

import time
from dataclasses import replace

import pytest
from afrp_runtime.common.errors import ConfigurationError, ContractViolationError
from afrp_runtime.contracts.cio import (
    AuthorizationVerdict,
    AuthorizedAction,
    ExecutionEventKind,
    ExecutionReport,
    OrderState,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer5.execution import (
    InMemoryOrderEventStore,
    OrderGateway,
    PortfolioReconciler,
    legal_order_targets,
)


def action(
    *,
    direction: float = 1.0,
    size: float = 2.0,
    verdict: AuthorizationVerdict = AuthorizationVerdict.AUTHORIZED,
) -> AuthorizedAction:
    return AuthorizedAction(
        envelope=make_envelope(
            producer_subsystem_id="L4-VAL",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-02",
            payload_repr=f"{direction}:{size}",
            trace_id="trace-order-1",
            generated_at_ns=1,
        ),
        candidate_id="candidate-1",
        verdict=verdict,
        instrument="XAUUSD",
        direction=direction,
        size=size,
        entry_price=2400.0,
        stop_price=2380.0 if direction > 0 else 2420.0,
        mission_profile_id="MP-02",
        constraint_diagnostics=(),
        hmac_signature=b"signed-action",
    )


def report(
    order_id: str,
    event: ExecutionEventKind,
    *,
    quantity: float = 0.0,
    price: float = 0.0,
    at_ns: int = 2,
) -> ExecutionReport:
    return ExecutionReport(
        envelope=make_envelope(
            producer_subsystem_id="VENUE-SIM",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-02",
            payload_repr=f"{order_id}:{event.name}:{quantity}",
            trace_id="trace-order-1",
            generated_at_ns=at_ns,
        ),
        order_id=order_id,
        event=event,
        fill_quantity=quantity,
        fill_price=price,
        venue="SIM",
        venue_at_ns=at_ns,
        reason="",
    )


@pytest.fixture(autouse=True)
def _audit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "layer5-test-key")


def gateway() -> tuple[OrderGateway, InMemoryOrderEventStore]:
    store = InMemoryOrderEventStore()
    instance = OrderGateway(
        "MP-02", event_store=store, order_id_factory=lambda: "order-1"
    )
    return instance, store


class TestOrderStateModel:
    def test_transition_table_has_terminal_dead_ends(self) -> None:
        for state in (
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
        ):
            assert legal_order_targets(state) == ()

    def test_submit_persists_and_audits_new_and_submitted(self) -> None:
        instance, store = gateway()
        intent = instance.submit(action(), at_ns=1)
        assert intent.state is OrderState.SUBMITTED
        assert [event[1] for event in store.events] == ["NEW", "SUBMITTED"]
        assert len(instance.audit_ledger.entries) == 2
        assert all(instance.audit_ledger.verify(e) for e in instance.audit_ledger.entries)
        assert intent.envelope.trace_id == "trace-order-1"

    @pytest.mark.parametrize(
        "verdict",
        [
            AuthorizationVerdict.NULL_TRADE,
            AuthorizationVerdict.REJECTED,
            AuthorizationVerdict.UNSPECIFIED,
        ],
    )
    def test_non_authorized_action_never_submits(
        self, verdict: AuthorizationVerdict
    ) -> None:
        instance, _ = gateway()
        with pytest.raises(ContractViolationError):
            instance.submit(action(verdict=verdict), at_ns=1)

    def test_missing_audit_key_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AFRP_AUDIT_HMAC_KEY", raising=False)
        with pytest.raises(ConfigurationError):
            OrderGateway("MP-02")

    def test_ack_partial_fill_final_fill(self) -> None:
        instance, store = gateway()
        submitted = instance.submit(action(), 1)
        acknowledged = instance.apply_report(
            report(submitted.order_id, ExecutionEventKind.ACK)
        )
        partial = instance.apply_report(
            report(
                submitted.order_id,
                ExecutionEventKind.PARTIAL_FILL,
                quantity=0.75,
                price=2401.0,
                at_ns=3,
            )
        )
        filled = instance.apply_report(
            report(
                submitted.order_id,
                ExecutionEventKind.FILL,
                quantity=1.25,
                price=2402.0,
                at_ns=4,
            )
        )
        assert acknowledged.state is OrderState.ACKNOWLEDGED
        assert partial.state is OrderState.PARTIALLY_FILLED
        assert filled.state is OrderState.FILLED
        record = instance.record(submitted.order_id)
        assert record.filled_quantity == pytest.approx(2.0)
        assert record.average_fill_price == pytest.approx(2401.625)
        assert len(store.events) == 5

    def test_immediate_fill_from_submitted_allowed(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(size=1.0), 1)
        filled = instance.apply_report(
            report(
                submitted.order_id,
                ExecutionEventKind.FILL,
                quantity=1.0,
                price=2400.5,
            )
        )
        assert filled.state is OrderState.FILLED

    @pytest.mark.parametrize(
        ("event", "state"),
        [
            (ExecutionEventKind.REJECT, OrderState.REJECTED),
            (ExecutionEventKind.EXPIRE, OrderState.EXPIRED),
            (ExecutionEventKind.CANCEL, OrderState.CANCELLED),
        ],
    )
    def test_terminal_venue_events(
        self, event: ExecutionEventKind, state: OrderState
    ) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(), 1)
        terminal = instance.apply_report(report(submitted.order_id, event))
        assert terminal.state is state
        with pytest.raises(ContractViolationError):
            instance.apply_report(report(submitted.order_id, ExecutionEventKind.ACK))

    def test_local_cancel(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(), 1)
        assert instance.cancel(submitted.order_id, 2).state is OrderState.CANCELLED

    def test_overfill_rejected(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(size=1.0), 1)
        with pytest.raises(ContractViolationError, match="overfill"):
            instance.apply_report(
                report(
                    submitted.order_id,
                    ExecutionEventKind.FILL,
                    quantity=1.1,
                    price=2400.0,
                )
            )

    def test_partial_fill_must_leave_remainder(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(size=1.0), 1)
        with pytest.raises(ContractViolationError, match="leave unfilled"):
            instance.apply_report(
                report(
                    submitted.order_id,
                    ExecutionEventKind.PARTIAL_FILL,
                    quantity=1.0,
                    price=2400.0,
                )
            )
        record = instance.record(submitted.order_id)
        assert record.state is OrderState.SUBMITTED
        assert record.filled_quantity == 0.0

    def test_final_fill_must_complete_quantity(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(size=1.0), 1)
        with pytest.raises(ContractViolationError, match="leaves quantity"):
            instance.apply_report(
                report(
                    submitted.order_id,
                    ExecutionEventKind.FILL,
                    quantity=0.5,
                    price=2400.0,
                )
            )
        record = instance.record(submitted.order_id)
        assert record.state is OrderState.SUBMITTED
        assert record.filled_quantity == 0.0

    def test_non_fill_event_cannot_carry_quantity(self) -> None:
        instance, _ = gateway()
        submitted = instance.submit(action(), 1)
        with pytest.raises(ContractViolationError, match="zero fill"):
            instance.apply_report(
                report(
                    submitted.order_id,
                    ExecutionEventKind.ACK,
                    quantity=0.1,
                    price=2400.0,
                )
            )

    def test_unknown_order_rejected(self) -> None:
        instance, _ = gateway()
        with pytest.raises(ContractViolationError, match="unknown order"):
            instance.apply_report(report("ghost", ExecutionEventKind.ACK))

    def test_audit_tamper_detected(self) -> None:
        instance, _ = gateway()
        instance.submit(action(), 1)
        entry = instance.audit_ledger.entries[0]
        assert not instance.audit_ledger.verify(replace(entry, event="TAMPERED"))


class TestRecovery:
    def test_order_checkpoint_restore_under_rto(self) -> None:
        source, _ = gateway()
        original = action()
        intent = source.submit(original, 1)
        checkpoint = source.snapshot(intent.order_id, 2)

        started = time.perf_counter()
        restored = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "unused",
        )
        restored.restore_order(checkpoint, original)
        elapsed = time.perf_counter() - started

        assert restored.record(intent.order_id).state is OrderState.SUBMITTED
        assert elapsed < 60.0

    def test_checkpoint_action_mismatch_rejected(self) -> None:
        source, _ = gateway()
        original = action()
        checkpoint = source.submit(original, 1)
        other = replace(
            original,
            envelope=make_envelope(
                producer_subsystem_id="L4-VAL",
                cognitive_cycle_id="c2",
                mission_profile_id="MP-02",
                payload_repr="other",
            ),
        )
        target, _ = gateway()
        with pytest.raises(ContractViolationError, match="action id mismatch"):
            target.restore_order(checkpoint, other)


class TestPortfolioReconciliation:
    def test_long_fill_preserves_equity_at_fill_mark(self) -> None:
        instance, _ = gateway()
        intent = instance.submit(action(direction=1.0, size=1.0), 1)
        fill = report(
            intent.order_id,
            ExecutionEventKind.FILL,
            quantity=1.0,
            price=2400.0,
        )
        filled_intent = instance.apply_report(fill)
        reconciler = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        reconciler.apply_fill(filled_intent, fill)
        state = reconciler.snapshot({"XAUUSD": 2400.0}, 3)
        assert state.cash == pytest.approx(97_600.0)
        assert state.equity == pytest.approx(100_000.0)
        assert state.positions[0].quantity == pytest.approx(1.0)

    def test_short_fill_and_mark_to_market(self) -> None:
        instance = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "short-1",
        )
        intent = instance.submit(action(direction=-1.0, size=1.0), 1)
        fill = report(
            intent.order_id,
            ExecutionEventKind.FILL,
            quantity=1.0,
            price=2400.0,
        )
        filled_intent = instance.apply_report(fill)
        reconciler = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        reconciler.apply_fill(filled_intent, fill)
        state = reconciler.snapshot({"XAUUSD": 2390.0}, 3)
        assert state.positions[0].quantity == pytest.approx(-1.0)
        assert state.positions[0].unrealized_pnl == pytest.approx(10.0)
        assert state.equity == pytest.approx(100_010.0)

    def test_weighted_average_for_same_direction_fills(self) -> None:
        reconciler = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        instance, _ = gateway()
        intent = instance.submit(action(size=2.0), 1)
        first = report(
            intent.order_id,
            ExecutionEventKind.PARTIAL_FILL,
            quantity=0.5,
            price=2400.0,
            at_ns=2,
        )
        partial_intent = instance.apply_report(first)
        reconciler.apply_fill(partial_intent, first)
        second = report(
            intent.order_id,
            ExecutionEventKind.FILL,
            quantity=1.5,
            price=2404.0,
            at_ns=3,
        )
        final_intent = instance.apply_report(second)
        reconciler.apply_fill(final_intent, second)
        state = reconciler.snapshot({"XAUUSD": 2403.0}, 4)
        assert state.positions[0].average_price == pytest.approx(2403.0)

    def test_non_fill_does_not_reconcile(self) -> None:
        instance, _ = gateway()
        intent = instance.submit(action(), 1)
        ack = report(intent.order_id, ExecutionEventKind.ACK)
        with pytest.raises(ContractViolationError):
            PortfolioReconciler("MP-02", 100_000.0).apply_fill(intent, ack)

    def test_missing_mark_rejected(self) -> None:
        reconciler = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        instance, _ = gateway()
        intent = instance.submit(action(size=1.0), 1)
        fill = report(
            intent.order_id,
            ExecutionEventKind.FILL,
            quantity=1.0,
            price=2400.0,
        )
        reconciler.apply_fill(instance.apply_report(fill), fill)
        with pytest.raises(ContractViolationError, match="mark"):
            reconciler.snapshot({}, 3)

    def test_portfolio_checkpoint_restore_under_rto(self) -> None:
        state = PortfolioReconciler("MP-02", 100_000.0).snapshot({}, 1)
        started = time.perf_counter()
        target = PortfolioReconciler("MP-02", 0.0)
        target.restore(state)
        restored = target.snapshot({}, 2)
        elapsed = time.perf_counter() - started
        assert restored.cash == pytest.approx(100_000.0)
        assert elapsed < 60.0
