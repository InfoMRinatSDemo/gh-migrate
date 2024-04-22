import click

from ..workbook import *
from git import Repo
from migrate.version import before_and_after_command


@click.command()
@before_and_after_command("./report/InfoMagnus - Migration Workbook.xlsx")
def start():

    print(f"*** Initializing migration workbook")
    initialize_workbook()

    # breakpoint()
