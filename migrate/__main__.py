import click
from .commands.diff import diff

@click.group()
def cli():
    pass

cli.add_command(diff)

if __name__ == "__main__":
    cli()