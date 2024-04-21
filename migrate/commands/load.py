import os
import click
import pandas as pd

from openpyxl import load_workbook
from ..workbook import *


@click.group()
def load():
    pass


@load.command()
@click.argument("before-source", required=False, default="./logs/before-source.csv")
@click.argument("before-target", required=False, default="./logs/before-target.csv")
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="report/InfoMagnus - Migration Workbook.xlsx",
)
def inventory(before_source, before_target, workbook_path):
    "" ""

    workbook = load_workbook(workbook_path)
    workbook.filename = workbook_path
    print(f"** Found workbook at: {workbook_path}")

    source_stats = pd.read_csv(
        before_source,
        parse_dates=["updatedAt", "pushedAt"],
    )
    print(f"*** Loading inventory")
    add_inventory_worksheet(workbook, "Inventory - Source Repos", source_stats)

    # If before_file exists
    if os.path.exists(before_target):
        target_stats = pd.read_csv(
            before_target,
            parse_dates=["updatedAt", "pushedAt"],
        )

        add_inventory_worksheet(workbook, "Inventory - Target Repos", target_stats)

    print(f"*** Generating pre-migration report")
    add_pre_migration_report(workbook, "Pre-migration Report", source_stats)
    print(f"*** Adding org mapping")
    add_org_mapping(workbook, "Mapping - Org", source_stats)

    print(f"*** Migratino workbook updated")
