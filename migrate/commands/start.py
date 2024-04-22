import click

from ..workbook import *
from git import Repo
from migrate.version import snapshot_before_after


@click.command()
@snapshot_before_after()
def start():

    print(f"*** Initializing migration workbook")
    initialize_workbook()

    # breakpoint()
