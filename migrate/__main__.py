import click
from .commands.diff import diff
from .commands.stats import stats

@click.group()
def cli():
    pass

cli.add_command(diff)
cli.add_command(stats)

if __name__ == "__main__":
    cli()