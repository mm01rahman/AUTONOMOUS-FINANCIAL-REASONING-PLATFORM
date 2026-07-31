"""AFRP Engineering OS command-line interface (WP-IMP-0003).

Registers the ``afrp`` command group. Commands are added per capability as
their Work Packages complete (EOS-002 toolchain order).
"""

from __future__ import annotations

import click
from afrp.commands.boot import boot_command
from afrp.commands.evidence import evidence_command
from afrp.commands.plan import plan_command
from afrp.commands.validate import validate_command


@click.group(name="afrp")
@click.version_option(version="0.1.0", prog_name="afrp")
def cli() -> None:
    """AFRP Engineering Operating System toolchain."""


cli.add_command(boot_command)
cli.add_command(plan_command)
cli.add_command(validate_command)
cli.add_command(evidence_command)


def main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":
    main()
