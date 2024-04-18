import click
from ..workbook import *


@click.command()
def start():
    print(f"*** Initializing migration workbook")

    initialize_workbook()
