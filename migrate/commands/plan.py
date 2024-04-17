import os
import click
import pandas as pd

from openpyxl import load_workbook
from ..workbook import add_inventory_worksheet, add_pre_migration_report


@click.command()
@click.argument("before-source", required=True)
def plan(before_source):
    print(f"*** Initializing migration workbook")

    workbook = load_workbook(os.path.join("report", "template", "workbook.xlsx"))

    # Read in initial source stats csv
    stats = pd.read_csv(
        before_source,
        parse_dates=["updatedAt", "pushedAt"],
    )

    add_inventory_worksheet(workbook, stats)
    add_pre_migration_report(workbook, stats)
