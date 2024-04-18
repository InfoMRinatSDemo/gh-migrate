import os
import click
import pandas as pd

from openpyxl import load_workbook
from ..workbook import *


@click.group()
def update():
    pass


@update.command()
@click.argument("before-source", required=False, default="report/before-source.csv")
@click.argument("before-target", required=False, default="report/before-target.csv")
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="report/InfoMagnus - Migration Workbook.xlsx",
)
def inventory(before_source, before_target, workbook_path):
    print(f"*** Updating migration workbook inventory")

    workbook = load_workbook(workbook_path)
    workbook.filename = workbook_path

    source_stats = pd.read_csv(
        before_source,
        parse_dates=["updatedAt", "pushedAt"],
    )
    add_inventory_worksheet(workbook, "Inventory - Source Repos", source_stats)

    # If before_file exists
    if os.path.exists(before_target):
        target_stats = pd.read_csv(
            before_target,
            parse_dates=["updatedAt", "pushedAt"],
        )

        add_inventory_worksheet(workbook, "Inventory - Target Repos", target_stats)

    add_pre_migration_report(workbook, "Pre-migration Report", source_stats)

    add_org_mapping(workbook, "Mapping - Org", source_stats)
