import click
from .commands.start import start
from .commands.diff import diff
from .commands.stats import stats
from .commands.update import update
from .commands.scripts import scripts


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(diff)
cli.add_command(stats)
cli.add_command(update)
cli.add_command(scripts)

if __name__ == "__main__":
    cli()
