import click
from .commands.start import start
from .commands.report import report
from .commands.stats import stats
from .commands.load import load
from .commands.scripts import scripts
from .commands.get import get


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(report)
cli.add_command(stats)
cli.add_command(load)
cli.add_command(scripts)
cli.add_command(get)

if __name__ == "__main__":
    cli()
