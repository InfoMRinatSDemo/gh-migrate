import click
from .commands.start import start
from .commands.get import get
from .commands.stats import stats
from .commands.load import load
from .commands.scripts import scripts
from .commands.check import check


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(get)
cli.add_command(stats)
cli.add_command(load)
cli.add_command(scripts)
cli.add_command(check)

if __name__ == "__main__":
    cli()
