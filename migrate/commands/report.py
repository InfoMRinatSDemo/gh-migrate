import os
import click
import pandas as pd
from datetime import datetime


@click.command()
@click.argument("before-source", type=click.STRING)
@click.argument("after-target", type=click.STRING)
@click.argument("after-source", type=click.STRING)
@click.argument("output", type=click.STRING)
def report(before_source, after_target, after_source, output=None):
    print("Diffing {} and {}".format(before_source, after_target))

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

    compare_dfs(
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
    pd.DataFrame(diffs).to_csv(output, index=False)


def parse_org_log(org, output_dir):
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

        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

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
    # timing_df.to_csv(f"{org}_timing_results.csv", index=False)

    # Write results to csv
    results_df = pd.DataFrame(results)
    # results_df.to_csv(f"{org}_results.csv", index=False)

    return (timing_df, results_df)


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

    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

    return (start_time, end_time, int((end_time - start_time).total_seconds() / 60))


def get_pat(type):
    if type == "source":
        return os.environ["GH_SOURCE_PAT"]
    elif type == "target":
        return os.environ["GH_TARGET_PAT"]
    else:
        raise ValueError('Type must be "source" or "target"')


def get_issues(github, repo):
    yield from get_nodes(
        github,
        "issues",
        {
            "owner": repo["owner"]["login"],
            "name": repo["name"],
            "pageSize": 100,
            "endCursor": None,
        },
        ["repository", "issues"],
    )


def get_pulls(github, repo):
    yield from get_nodes(
        github,
        "pulls",
        {
            "owner": repo["owner"]["login"],
            "name": repo["name"],
            "pageSize": 100,
            "endCursor": None,
        },
        ["repository", "pullRequests"],
    )


def get_repos(github, org):
    yield from get_nodes(
        github,
        "org-repos",
        {"login": org, "pageSize": 10, "endCursor": None},
        ["organization", "repositories"],
    )


def get_nodes(github, query_name, variables, page_path):
    """Retrieves all nodes from a paginated GraphQL query"""

    @lru_cache(maxsize=None)
    def get_query(name):
        with open(f"migrate/graphql/{name}.graphql") as f:
            return f.read()

    # https://stackoverflow.com/questions/71460721/best-way-to-get-nested-dictionary-items
    def get_nested_item(d, key):
        for level in key:
            d = d[level]
        return d

    query = get_query(query_name)

    while True:
        response = github.graphql(query, variables=variables)

        # Print errors and exit if any found
        if "errors" in response:
            for error in response["errors"]:
                print(f"Error: {error['message']}")
            return

        items = get_nested_item(response, page_path)
        for item in items["nodes"]:
            yield item

        # Exit if no more pages
        if not items["pageInfo"]["hasNextPage"]:
            break

        # Otherwise, update the endCursor and continue
        variables["endCursor"] = items["pageInfo"]["endCursor"]
