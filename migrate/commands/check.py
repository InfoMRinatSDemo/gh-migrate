import click
import pandas as pd

import os
import base64
from functools import lru_cache
from githubkit import GitHub

# from tqdm import tqdm


@click.command()
@click.option("-t", "--target-org", "target_orgs", multiple=True, required=False)
@click.option("-tp", "--target-pat", "target_pat", required=False)
@click.option("-o", "--output", "output", required=True)
def check(target_orgs, target_pat, output):
    print(f"* Checking {target_orgs}")

    if target_orgs is not None:
        for org in target_orgs:
            print(f"\n* Processing org {org}")
            github = GitHub(target_pat)
            process_org(github, "target", org, output)


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
    import subprocess

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
    parse_org_log(output_dir)

    # Parse the repository migration logs
    parse_repo_logs(f"./{output_dir}/success")


def parse_repo_logs(output_dir):
    import os

    # Get all the directories in the output_dir
    repos = [repo for repo in os.listdir(output_dir)]

    for repo_log in repos:
        # Open file and find lines starting with '['
        with open(f"{output_dir}/{repo_log}", "r") as f:
            lines = [line for line in f.readlines() if line.startswith("[")]

        ############################################################
        # Print repo migration timing
        ############################################################

        # Get line containing "Repository migration started"
        start_line = [line for line in lines if "Migration started" in line][0]
        end_line = [line for line in lines if "Migration complete" in line][0]

        # Parse start time from start_line
        start_time = start_line.split(" ")[0]
        end_time = end_line.split(" ")[0]

        # Remove '[' and ']'
        start_time = start_time[1:-1]
        end_time = end_time[1:-1]

        # start_time contains a string like "2024-04-12T01:25:50Z"
        from datetime import datetime

        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

        print(f"Repo: {repo_log}")
        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Duration: {end_time - start_time}")

        ############################################################
        # Print warnings or errors
        ############################################################

        # Get lines containing "WARN" or "ERROR"
        warnings = [line for line in lines if "WARN" in line]
        errors = [line for line in lines if "ERROR" in line]

        if len(warnings) != 0:
            print("Warnings:")
            [print(warning) for warning in warnings]

        if len(errors) != 0:
            print("Errors:")
            [print(error) for error in errors]


def parse_org_log(output_dir):
    import os

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
    from datetime import datetime

    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

    print("The migration started at:", start_time)
    print("The migration ended at:", end_time)
    print("The migration took:", end_time - start_time)

    ############################################################
    # Get repos
    ############################################################
    # repos = get_repos(github, org)

    # for repo in repos:
    #     print(f'** Downloading migration log from "{repo["name"]}"')

    #     repo_name = repo["name"]
    #     org_name = repo["owner"]["login"]

    #     ############################################################
    #     # Get latest issue comment
    #     ############################################################
    #     response = github.rest.issues.list_comments_for_repo(org_name, repo_name)
    #     id = response.json()[0]["id"]

    #     comment = github.rest.issues.get_comment(org_name, repo_name, id)
    #     print(comment.json()["body"])

    #     # Get directory path
    #     output_path = os.path.join(output_dir, f"{org_name}-{repo_name}.csv")

    #     # Write issue comment to file
    #     with open(output_path, "w") as f:
    #         f.write(comment.json()["body"])


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
