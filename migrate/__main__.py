import click
from .commands.diff import diff
from .commands.stats import stats
from .commands.plan import plan


@click.group()
def cli():
    pass


cli.add_command(diff)
cli.add_command(stats)
cli.add_command(plan)

if __name__ == "__main__":
    cli()
