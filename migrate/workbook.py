import os
import pandas as pd

import pytz
import datetime

import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.table import TableStyleInfo

# Create a table style
table_style = TableStyleInfo(
    name="TableStyleMedium9", showFirstColumn=False, showLastColumn=False
)


def add_sheet(workbook, sheet_name, desired_index=0, tab_color="FF0000"):
    if sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
    else:
        worksheet = workbook.create_sheet(sheet_name, index=desired_index)
        worksheet.sheet_properties.tabColor = tab_color

    return worksheet


def autosize_columns(worksheet):
    for column in worksheet.columns:
        max_length = 0
        column = column[0].column_letter
        for cell in worksheet[column]:
            try:  # Necessary to avoid error on empty cells
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column].width = adjusted_width


def write_table(worksheet, df, table_name, heading=""):
    df["pushedAt"] = df["pushedAt"].dt.tz_localize(None)
    df["updatedAt"] = df["updatedAt"].dt.tz_localize(None)

    # Add a header with the table name
    if heading != "":
        worksheet.append([heading])
        worksheet[f"A{worksheet.max_row}"].font = Font(bold=True, size=12)

    # If there are no rows, add a single row with "No data"
    if df.empty:
        worksheet.append(["None"])
        worksheet[f"A{worksheet.max_row}"].font = Font(italic=True)
    else:
        # Add the table
        from openpyxl.worksheet.table import Table, TableStyleInfo

        num_rows, num_cols = df.shape
        if heading != "":
            start_col, start_row = "A", worksheet.max_row + 1
        else:
            start_col, start_row = "A", worksheet.max_row
        end_col = openpyxl.utils.get_column_letter(num_cols)
        end_row = start_row + num_rows

        table = Table(
            displayName=table_name,
            ref=f"{start_col}{start_row}:{end_col}{end_row}",
            tableStyleInfo=table_style,
        )
        worksheet.add_table(table)

        # Add the data
        worksheet.append(df.columns.to_list())
        for row in df.itertuples(index=False, name=None):
            worksheet.append(row)

        # Group added rows
        worksheet.row_dimensions.group(start_row + 1, end_row, hidden=False)
        autosize_columns(worksheet)

    # Move to the next empty row
    worksheet.append([])


def add_inventory_worksheet(workbook, stats):
    """ """
    desired_index = workbook.sheetnames.index("Cover") + 1
    worksheet = add_sheet(workbook, "Inventory", desired_index, "002060")

    # Clear the contents of the worksheet
    worksheet.delete_rows(1, worksheet.max_row)

    write_table(worksheet, stats, "Inventory")


def add_pre_migration_report(workbook, stats):
    """ """

    desired_index = workbook.sheetnames.index("Cover") + 1
    worksheet = add_sheet(workbook, "Pre-migration report", desired_index, "215C98")

    # Clear the contents of the worksheet
    worksheet.delete_rows(1, worksheet.max_row)

    # Create large repos table
    df = stats[stats["diskUsage"] > 1000].sort_values(by="diskUsage")
    write_table(worksheet, df, "Large_Repos", "Large Repos")

    # Create large PRs table
    df = stats[stats["pullRequests.totalCount"] > 1000].sort_values(
        by="pullRequests.totalCount"
    )
    write_table(worksheet, df, "Large_PRs", "Large PRs")

    # Create webhooks table
    df = stats[stats["webhooks.totalCount"] > 0].sort_values(by="webhooks.totalCount")
    write_table(worksheet, df, "Webhooks_Repos", "Repos with webhooks")

    # Create actions table
    df = stats[stats["lastWorkflowRun"] != None].sort_values("lastWorkflowRun")
    write_table(worksheet, df, "Actions_Repos", "Repos with actions")

    # Create stale repos table
    stats["pushedAt"] = stats["pushedAt"].dt.tz_localize("UTC")
    df = stats[
        stats["pushedAt"]
        < datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=60)
    ].sort_values("pushedAt")
    write_table(worksheet, df, "Stale_Repos", "Stale Repos")

    # Create archived repos table
    df = stats[stats["isArchived"] == True].sort_values("isArchived")
    write_table(worksheet, df, "Archived_Repos", "Archived Repos")

    # Create locked repos table
    df = stats[stats["isLocked"] == True].sort_values("isLocked")
    write_table(worksheet, df, "Locked_Repos", "Locked Repos")

    # Create repos with packages table
    df = stats[stats["packages.totalCount"] > 0].sort_values("packages.totalCount")
    write_table(worksheet, df, "Has_Packages", "Repos with packages")

    # def identify_git_lfs():
    # # TODO: Need to figure out how to implement this

    # Save the workbook to a file called 'test.xlsx'
    workbook.save(os.path.join("report", "InfoMagnus - Migration Workbook.xlsx"))
