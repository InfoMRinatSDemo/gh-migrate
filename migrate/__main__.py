import click
from .commands.start import start
from .commands.diff import diff
from .commands.stats import stats
from .commands.plan import plan
from .commands.scripts import scripts


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(diff)
cli.add_command(stats)
cli.add_command(plan)
cli.add_command(scripts)

if __name__ == "__main__":
    cli()
