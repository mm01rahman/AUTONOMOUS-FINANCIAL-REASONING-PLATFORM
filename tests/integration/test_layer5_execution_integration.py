"""WP-RT-1017 integration tests for the full Layer 5 execution pipeline."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    AuthorizationVerdict,
    AuthorizedAction,
    ExecutionEventKind,
    OrderState,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer5.execution import (
    InMemoryOrderEventStore,
    OrderGateway,
    PortfolioReconciler,
)


@pytest.fixture(autouse=True)
def _audit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "layer5-integration-test-key")


def _authorized_action(
    direction: float = 1.0,
    size: float = 1.0,
    entry: float = 2400.0,
    stop: float = 2380.0,
) -> AuthorizedAction:
    env = make_envelope(
        "L4-VAL", "c1", "MP-02", f"auth:{direction}:{size}", trace_id="trace-integ"
    )
    return AuthorizedAction(
        envelope=env,
        candidate_id="cand-integ",
        verdict=AuthorizationVerdict.AUTHORIZED,
        instrument="XAUUSD",
        direction=direction,
        size=size,
        entry_price=entry,
        stop_price=stop,
        mission_profile_id="MP-02",
        constraint_diagnostics=(),
        hmac_signature=b"integration-sig-valid",
    )


class TestFullOrderLifecycle:
    """End-to-end order lifecycle: submit → ACK → PARTIAL_FILL → FILL → portfolio."""

    def test_complete_long_order_reconciles_portfolio(self) -> None:
        store = InMemoryOrderEventStore()
        gw = OrderGateway(
            "MP-02", event_store=store, order_id_factory=lambda: "ORD-INTEG-001"
        )
        rec = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        action = _authorized_action(direction=1.0, size=2.0)

        submitted = gw.submit(action, at_ns=1_000)

        ack_env = make_envelope("VENUE", "c1", "MP-02", "ack", trace_id="trace-integ")
        from afrp_runtime.contracts.cio import ExecutionReport

        ack = ExecutionReport(
            envelope=ack_env,
            order_id=submitted.order_id,
            event=ExecutionEventKind.ACK,
            fill_quantity=0.0,
            fill_price=0.0,
            venue="SIM",
            venue_at_ns=2_000,
            reason="",
        )
        acknowledged = gw.apply_report(ack)
        assert acknowledged.state is OrderState.ACKNOWLEDGED

        partial_env = make_envelope("VENUE", "c1", "MP-02", "pf:0.75", trace_id="trace-integ")
        partial = ExecutionReport(
            envelope=partial_env,
            order_id=submitted.order_id,
            event=ExecutionEventKind.PARTIAL_FILL,
            fill_quantity=0.75,
            fill_price=2401.0,
            venue="SIM",
            venue_at_ns=3_000,
            reason="",
        )
        partial_intent = gw.apply_report(partial)
        assert partial_intent.state is OrderState.PARTIALLY_FILLED
        rec.apply_fill(partial_intent, partial)

        fill_env = make_envelope("VENUE", "c1", "MP-02", "fill:1.25", trace_id="trace-integ")
        fill = ExecutionReport(
            envelope=fill_env,
            order_id=submitted.order_id,
            event=ExecutionEventKind.FILL,
            fill_quantity=1.25,
            fill_price=2402.0,
            venue="SIM",
            venue_at_ns=4_000,
            reason="",
        )
        filled_intent = gw.apply_report(fill)
        assert filled_intent.state is OrderState.FILLED
        rec.apply_fill(filled_intent, fill)

        state = rec.snapshot({"XAUUSD": 2405.0}, at_ns=5_000)

        expected_cash = 100_000.0 - (0.75 * 2401.0 + 1.25 * 2402.0)
        assert state.cash == pytest.approx(expected_cash)
        assert state.positions[0].quantity == pytest.approx(2.0)
        expected_avg = (0.75 * 2401.0 + 1.25 * 2402.0) / 2.0
        assert state.positions[0].average_price == pytest.approx(expected_avg)
        assert state.positions[0].unrealized_pnl == pytest.approx((2405.0 - expected_avg) * 2.0)

        # Verify all audit entries are tamper-proof
        assert all(gw.audit_ledger.verify(e) for e in gw.audit_ledger.entries)

        # 5 events: NEW, SUBMITTED, ACK, PARTIAL_FILL, FILL
        assert len(store.events) == 5

    def test_complete_short_order_recognizes_pnl(self) -> None:
        gw = OrderGateway(
            "MP-02", event_store=InMemoryOrderEventStore(), order_id_factory=lambda: "ORD-SHORT"
        )
        rec = PortfolioReconciler("MP-02", initial_cash=100_000.0)
        action = _authorized_action(direction=-1.0, size=1.0, entry=2400.0, stop=2420.0)
        submitted = gw.submit(action, at_ns=1_000)

        from afrp_runtime.contracts.cio import ExecutionReport

        fill_env = make_envelope("VENUE", "c1", "MP-02", "fill:1.0", trace_id="trace-short")
        fill = ExecutionReport(
            envelope=fill_env,
            order_id=submitted.order_id,
            event=ExecutionEventKind.FILL,
            fill_quantity=1.0,
            fill_price=2400.0,
            venue="SIM",
            venue_at_ns=2_000,
            reason="",
        )
        filled = gw.apply_report(fill)
        rec.apply_fill(filled, fill)

        # Mark drops: short position profits
        state = rec.snapshot({"XAUUSD": 2380.0}, at_ns=3_000)
        assert state.positions[0].quantity == pytest.approx(-1.0)
        assert state.positions[0].unrealized_pnl == pytest.approx(20.0)
        assert state.equity == pytest.approx(100_020.0)

    def test_cancel_flow(self) -> None:
        gw = OrderGateway(
            "MP-02", event_store=InMemoryOrderEventStore(), order_id_factory=lambda: "ORD-CANCEL"
        )
        action = _authorized_action()
        submitted = gw.submit(action, at_ns=1_000)
        cancelled = gw.cancel(submitted.order_id, at_ns=2_000)
        assert cancelled.state is OrderState.CANCELLED

        from afrp_runtime.contracts.cio import ExecutionReport

        fill_env = make_envelope("VENUE", "c1", "MP-02", "fill:1.0", trace_id="trace-cancel")
        with pytest.raises(ContractViolationError):
            gw.apply_report(
                ExecutionReport(
                    envelope=fill_env,
                    order_id=submitted.order_id,
                    event=ExecutionEventKind.FILL,
                    fill_quantity=1.0,
                    fill_price=2400.0,
                    venue="SIM",
                    venue_at_ns=3_000,
                    reason="",
                )
            )


class TestRecoveryIntegration:
    """Order and portfolio checkpoint recovery integration tests."""

    def test_order_restore_from_checkpoint(self) -> None:
        gw_orig = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "ORD-CKPT",
        )
        action = _authorized_action(size=2.0)
        intent = gw_orig.submit(action, at_ns=1_000)
        checkpoint = gw_orig.snapshot(intent.order_id, at_ns=1_500)

        gw_restored = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "unused",
        )
        gw_restored.restore_order(checkpoint, action)
        rec = gw_restored.record(intent.order_id)
        assert rec.state is OrderState.SUBMITTED
        assert rec.filled_quantity == pytest.approx(0.0)

    def test_portfolio_restore_from_checkpoint(self) -> None:
        gw = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "ORD-PORT-CKPT",
        )
        rec = PortfolioReconciler("MP-02", initial_cash=50_000.0)
        action = _authorized_action(size=1.0)
        submitted = gw.submit(action, at_ns=1_000)

        from afrp_runtime.contracts.cio import ExecutionReport

        fill_env = make_envelope("VENUE", "c1", "MP-02", "fill:1.0", trace_id="trace-ckpt")
        fill = ExecutionReport(
            envelope=fill_env,
            order_id=submitted.order_id,
            event=ExecutionEventKind.FILL,
            fill_quantity=1.0,
            fill_price=2400.0,
            venue="SIM",
            venue_at_ns=2_000,
            reason="",
        )
        rec.apply_fill(gw.apply_report(fill), fill)
        checkpoint_state = rec.snapshot({"XAUUSD": 2400.0}, at_ns=3_000)

        rec2 = PortfolioReconciler("MP-02", initial_cash=0.0)
        rec2.restore(checkpoint_state)
        restored_state = rec2.snapshot({"XAUUSD": 2410.0}, at_ns=4_000)
        assert restored_state.cash == pytest.approx(checkpoint_state.cash)
        assert restored_state.positions[0].quantity == pytest.approx(1.0)
        assert restored_state.positions[0].unrealized_pnl == pytest.approx(10.0)

    def test_audit_integrity_across_full_lifecycle(self) -> None:
        gw = OrderGateway(
            "MP-02",
            event_store=InMemoryOrderEventStore(),
            order_id_factory=lambda: "ORD-AUDIT",
        )
        action = _authorized_action(size=1.0)
        submitted = gw.submit(action, at_ns=1_000)

        from afrp_runtime.contracts.cio import ExecutionReport

        for event_kind, qty, price, ns in [
            (ExecutionEventKind.ACK, 0.0, 0.0, 2_000),
            (ExecutionEventKind.FILL, 1.0, 2400.0, 3_000),
        ]:
            env = make_envelope(
                "VENUE", "c1", "MP-02", f"{event_kind.name}", trace_id="trace-audit"
            )
            rpt = ExecutionReport(
                envelope=env,
                order_id=submitted.order_id,
                event=event_kind,
                fill_quantity=qty,
                fill_price=price,
                venue="SIM",
                venue_at_ns=ns,
                reason="",
            )
            gw.apply_report(rpt)

        assert gw.record(submitted.order_id).state is OrderState.FILLED
        # Every audit entry must pass HMAC verification
        assert len(gw.audit_ledger.entries) == 4  # NEW, SUBMITTED, ACK, FILL
        assert all(gw.audit_ledger.verify(e) for e in gw.audit_ledger.entries)
