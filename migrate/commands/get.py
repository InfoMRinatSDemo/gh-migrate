import click
import pandas as pd

import os
from functools import lru_cache
from githubkit import GitHub

import subprocess
from datetime import datetime


@click.command()
@click.option("-t", "--target-org", "target_orgs", multiple=True, required=False)
@click.option("-tp", "--target-pat", "target_pat", required=False)
@click.option("-o", "--output", "output", required=True)
def get(target_orgs, target_pat, output):
    print(f"* Checking {target_orgs}")

    org_timings = []
    repo_timings = []
    repo_results = []

    if target_orgs is not None:
        for org in target_orgs:
            print(f"\n* Processing org {org}")
            github = GitHub(target_pat)
            (start_time, end_time, duration, repo_timing, repo_result) = process_org(
                github, "target", org, output
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
            repo_results.append(repo_results)

    # Save the timings
    org_timings_df = pd.DataFrame(org_timings)
    org_timings_df.to_csv(f"{output}/org_timings.csv", index=False)

    # Combine dataframes in arepo_timings and arepo_results
    repo_timings_df = pd.concat(repo_timings)
    repo_results_df = pd.concat(repo_results)

    repo_timings_df.to_csv(f"{output}/repo_timings.csv", index=False)
    repo_results_df.to_csv(f"{output}/repo_results.csv", index=False)


###############################################################################
# We can grab the migration logs in the following ways:
#
# Within 1 day of migration, we can use the GH migration API to get the logs
#
# If the migration is older than 1 day:
# - If GEI 'migrate-org' was used
#   - we can get the logs from 'gei-migration-results' repo
# - If GEI 'migrate-repo' was used
#   - we can get the logs from the issue comment of the last issue in the repo
#
# The problem with retrieving logs from the issue comment is that if issues are
# not enabled in the repo, GEI will not be able to post the logs.
###############################################################################


def process_org(github: GitHub, source, org, output_dir):
    """Process all repos in an org"""

    # Try cloning 'gei-migration-results' repo using 'gh repo clone'

    output_dir = f"{output_dir}/{org}"

    # Define the command
    command = [
        "gh",
        "repo",
        "clone",
        f"https://github.com/{org}/gei-migration-results",
        output_dir,
    ]

    # Run the command
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print("Retrieved migration logs successfully!")
    else:
        print(f'Failed to retrieve migration logs: {result.stderr.decode("utf-8")}')

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
