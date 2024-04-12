import click
from . import commands

@click.group()
def cli():
    pass

cli.add_command(commands.diff)

if __name__ == "__main__":
    cli()