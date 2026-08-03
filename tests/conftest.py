"""Root conftest: register custom markers and hooks."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Also run tests marked as @pytest.mark.slow",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(
        reason="Slow campaign test — run with --run-slow to include"
    )
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
