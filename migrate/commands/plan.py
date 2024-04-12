import os
import click
import pandas as pd

from openpyxl import load_workbook
from ..workbook import add_inventory_worksheet, add_pre_migration_report


@click.command()
@click.argument("org-name", required=True)
@click.argument("before-source", required=True)
def plan(org_name, before_source):
    ##########################################################################
    # Main function
    ##########################################################################
    print(f"*** Generating reports for {org_name}")

    workbook = load_workbook(os.path.join("report", "template", "workbook.xlsx"))
    # Read in initial source stats csv
    stats = pd.read_csv(
        before_source,
        parse_dates=["updatedAt", "pushedAt"],
    )

    add_inventory_worksheet(workbook, stats)
    add_pre_migration_report(workbook, stats)
