import os
import click
import pandas as pd
from datetime import datetime

from migrate.workbook import *


@click.command()
@click.option("--dry-run", is_flag=True, help="Is this a dry-run?")
@click.option("--wave", type=int, help="Wave number", required=True)
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="report/InfoMagnus - Migration Workbook.xlsx",
)
@click.argument("output_dir", type=click.STRING, required=False, default="logs")
def report(dry_run, wave, workbook_path, output_dir):

    workbook = get_workbook(workbook_path)

    target_column = "target_name"

    if dry_run:
        output_dir = os.path.join(output_dir, "dry-run")
        target_column = "dry_run_target_name"

    orgs = get_included_orgs_by_wave(target_column, wave, workbook_path)

    ############################################################
    # Parse the GEI logs and generate the GEI migration reports
    ############################################################
    print(f"\n* Generating GEI migration reports for wave: {wave}")
    (org_timings, repo_timings, repo_results) = generate_gei_reports(orgs, output_dir)
    add_worksheet(workbook, f"Org Timings-{wave}", org_timings)
    add_worksheet(workbook, f"Repo Timings-{wave}", repo_timings)
    add_worksheet(workbook, f"Repo Results-{wave}", repo_results)
    workbook.save(workbook_path)

    ############################################################
    # Parse the `gh migrate stats` results and report any
    # differences between the source and target orgs
    ############################################################
    print(f"\n* Generating stats report for wave: {wave}")
    stats = generate_stats_report(workbook, wave, output_dir)
    add_worksheet(workbook, f"Migration Report-{wave}", stats)

    workbook.save(workbook_path)


def generate_gei_reports(orgs, logs_dir):

    org_timings = []
    repo_timings = []
    repo_results = []

    for org in orgs:
        print(f"\n** Processing org {org}")
        (start_time, end_time, duration, repo_timing, repo_result) = (
            parse_migration_logs(org, logs_dir)
        )

        org_timings.append(
            {
                "org": org,
                "start_time": start_time,
                "end_time": end_time,
                "duration (mins)": duration,
            }
        )
        repo_timings.append(repo_timing)
        repo_results.append(repo_result)

    org_timings_df = pd.DataFrame(org_timings)
    repo_timings_df = pd.concat(repo_timings)
    repo_results_df = pd.concat(repo_results)

    return (org_timings_df, repo_timings_df, repo_results_df)


def parse_migration_logs(org, output_dir):
    output_dir = f"{output_dir}/{org}"

    # Parse the organization migration log
    (start_time, end_time, duration) = parse_org_log(output_dir)

    # Parse the repository migration logs
    (success_repo_timing, success_repo_results) = parse_repo_logs(
        org, "success", f"./{output_dir}"
    )
    (fail_repo_timing, fail_repo_results) = parse_repo_logs(
        org, "failure", f"./{output_dir}"
    )

    repo_timing = pd.concat([success_repo_timing, fail_repo_timing])
    repo_results = pd.concat([success_repo_results, fail_repo_results])

    return (start_time, end_time, duration, repo_timing, repo_results)


def parse_org_log(output_dir):

    org_log = os.path.join("./", output_dir, "README.md")

    # Open file and find lines starting with '['
    with open(org_log, "r") as f:
        lines = [line for line in f.readlines() if line.startswith("[")]

    # Get line containing "Organization migrated started"
    start_line = [line for line in lines if "Organization migration started" in line][0]
    end_line = [line for line in lines if "Organization migration completed" in line][0]

    # Parse start time from start_line
    start_time = start_line.split(" ")[0]
    end_time = end_line.split(" ")[0]

    # Remove '[' and ']'
    start_time = start_time[1:-1]
    end_time = end_time[1:-1]

    # start_time contains a string like "2024-04-12T01:25:50Z"

    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

    return (start_time, end_time, int((end_time - start_time).total_seconds() / 60))


def parse_repo_logs(org, type, output_dir):

    timing = []
    results = []

    output_dir = f"{output_dir}/{type}"

    # Return if output_dir doesn't exist
    if not os.path.exists(output_dir):
        return pd.DataFrame(timing), pd.DataFrame(results)

    # Get all the directories in the output_dir
    repos = [repo for repo in os.listdir(output_dir)]

    for repo_log in repos:
        # Open file and find lines starting with '['
        with open(f"{output_dir}/{repo_log}", "r") as f:
            lines = [line for line in f.readlines() if line.startswith("[")]

        ############################################################
        # Get repo migration timing
        ############################################################

        # We should *always* have a start line
        start_line = [line for line in lines if "Migration started" in line]
        assert len(start_line) == 1
        start_line = start_line[0]

        if type == "success":
            end_line = [line for line in lines if "Migration complete" in line][0]
        elif type == "failure":
            end_line = [line for line in lines if "Migration failed" in line][0]

        # Parse start time from start_line
        start_time = start_line.split(" ")[0]
        end_time = end_line.split(" ")[0]

        # Remove '[' and ']'
        start_time = start_time[1:-1]
        end_time = end_time[1:-1]

        # start_time contains a string like "2024-04-12T01:25:50Z"

        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

        print(f"Repo: {repo_log}")

        timing.append(
            {
                "org": org,
                "repo": repo_log,
                "start_time": start_time,
                "end_time": end_time,
                "duration (mins)": int((end_time - start_time).total_seconds() / 60),
            }
        )

        ############################################################
        # Get warnings or errors
        ############################################################

        warnings = [line for line in lines if "WARN" in line]
        errors = [line for line in lines if "ERROR" in line]

        if len(warnings) != 0:
            for warning in warnings:
                results.append(
                    {
                        "org": org,
                        "repo": repo_log,
                        "type": "WARN",
                        "message": warning.strip(),
                    }
                )

        if len(errors) != 0:
            for error in errors:
                results.append(
                    {
                        "org": org,
                        "repo": repo_log,
                        "type": "ERROR",
                        "message": error.strip(),
                    }
                )

    # Write timing_results to csv
    timing_df = pd.DataFrame(timing)

    # Write results to csv
    results_df = pd.DataFrame(results)

    return (timing_df, results_df)


def generate_stats_report(workbook, wave, output):

    before_source = os.path.join(output, f"before-source-wave-{wave}.csv")
    after_target = os.path.join(output, f"after-target-wave-{wave}.csv")
    after_source = os.path.join(output, f"after-source-wave-{wave}.csv")

    before_source_stats = pd.read_csv(before_source, dtype=str)
    after_target_stats = pd.read_csv(after_target, dtype=str)
    after_source_stats = pd.read_csv(after_source, dtype=str)

    ignore_cols = [
        "createdAt",
        "pushedAt",
        "updatedAt",
        "url",
        "issues.comments.totalCount",
        "issues.timelineItems.totalCount",
    ]
    before_source_stats = before_source_stats.drop(columns=ignore_cols)
    after_target_stats = after_target_stats.drop(columns=ignore_cols)
    after_source_stats = after_source_stats.drop(columns=ignore_cols)

    return compare_dfs(
        "name", before_source_stats, after_target_stats, after_source_stats, output
    )


def compare_dfs(key, source_df, target_df, context_df, output):
    """
    Compare the before_source and after_target dataframes and write the differences to file
    """

    def not_equal(val1, val2):
        val1 = val1.lower() if isinstance(val1, str) else val1
        val2 = val2.lower() if isinstance(val2, str) else val2

        if pd.isna(val1) and pd.isna(val2):
            return False
        if pd.isna(val1) or pd.isna(val2):
            return True
        elif val1 != val2:
            return True
        else:
            return False

    def get_row(key, df, name):
        return df[df[key] == name]

    diffs = []

    for row in source_df.itertuples():
        source_row = get_row(key, source_df, row.name)
        target_row = get_row(key, target_df, row.name)
        context_row = get_row(key, context_df, row.name)

        if source_row.equals(target_row):
            continue
        elif source_row.empty or target_row.empty:
            continue
        else:
            for col in source_row.columns:
                if not_equal(source_row[col].values[0], target_row[col].values[0]):
                    diffs.append(
                        {
                            "source_name": f"{source_row['owner.login'].values[0]}/{source_row['name'].values[0]}",
                            "target_name": f"{target_row['owner.login'].values[0]}/{target_row['name'].values[0]}",
                            "column": col,
                            "source_value": source_row[col].values[0],
                            "target_value": target_row[col].values[0],
                            "context_value": context_row[col].values[0],
                            "source_date": source_row["Inventoried"].values[0],
                            "target_date": target_row["Inventoried"].values[0],
                            "context_date": context_row["Inventoried"].values[0],
                        }
                    )

    # Write the differences to a file
    return pd.DataFrame(diffs)
