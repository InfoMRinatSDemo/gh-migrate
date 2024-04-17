import click
import pandas as pd

import os
import base64
from functools import lru_cache
from githubkit import GitHub

# from tqdm import tqdm


@click.command()
@click.option("-s", "--source-org", "source_orgs", multiple=True, required=True)
@click.option("-sp", "--source-pat", "source_pat", required=True)
@click.option("-t", "--target-org", "target_orgs", multiple=True, required=False)
@click.option("-tp", "--target-pat", "target_pat", required=False)
@click.option("-o", "--output", "output", required=True)
def stats(source_orgs, source_pat, target_orgs, target_pat, output):
    print(f"* Inventorying {source_orgs} and {target_orgs}")

    if source_orgs is not None:
        for org in source_orgs:
            print(f"\n* Processing org {org}")
            github = GitHub(source_pat)
            process_org(github, "source", org, output)

    if target_orgs is not None:
        for org in target_orgs:
            print(f"\n* Processing org {org}")
            github = GitHub(target_pat)
            process_org(github, "target", org, output)


def process_org(github, source, org, output_file):
    """Process all repos in an org"""

    ############################################################
    # Recursively cleanup all pageInfos and nodes from repo dict
    ############################################################
    def cleanup_repo(d):
        if isinstance(d, dict):
            if "pageInfo" in d:
                del d["pageInfo"]
            if "nodes" in d:
                del d["nodes"]
            for k, v in d.items():
                cleanup_repo(v)
        elif isinstance(d, list):
            for i in d:
                cleanup_repo(i)

    ############################################################
    # Get repos
    ############################################################
    repos = get_repos(github, org)

    for repo in repos:
        print(f'** Processing repo "{repo["name"]}"')

        ############################################################
        # Get issues
        ############################################################
        issues = pd.DataFrame([issue for issue in get_issues(github, repo)])

        if len(issues) == 0:
            repo["issues"]["comments"] = {"totalCount": 0}
            repo["issues"]["timelineItems"] = {"totalCount": 0}
        else:
            # Sum comments
            repo["issues"]["comments"] = {
                "totalCount": sum([i["totalCount"] for i in issues["comments"]])
            }
            # Sum timelineItems
            repo["issues"]["timelineItems"] = {
                "totalCount": sum([i["totalCount"] for i in issues["timelineItems"]])
            }

        ############################################################
        # Get PRs
        ############################################################
        pulls = pd.DataFrame([pull for pull in get_pulls(github, repo)])

        if len(pulls) == 0:
            repo["pullRequests"]["comments"] = {"totalCount": 0}
            repo["pullRequests"]["commits"] = {"totalCount": 0}
            repo["pullRequests"]["timelineItems"] = {"totalCount": 0}
        else:
            # Sum comments
            repo["pullRequests"]["comments"] = {
                "totalCount": sum([i["totalCount"] for i in pulls["comments"]])
            }
            # Sum commits
            repo["pullRequests"]["commits"] = {
                "totalCount": sum([i["totalCount"] for i in pulls["commits"]])
            }
            # Sum timelineItems
            repo["pullRequests"]["timelineItems"] = {
                "totalCount": sum([i["totalCount"] for i in pulls["timelineItems"]])
            }

        # Add in the REST API stats
        get_rest_api_stats(github, repo)

        # Remove pageInfos and nodes
        cleanup_repo(repo)

        # Add source
        repo["Source"] = source

        # Add date and time
        repo["Inventoried"] = pd.Timestamp.now()

        # Normalize column headings
        repo = pd.json_normalize(repo)

        # Write to file
        with open(output_file, "a") as f:
            repo.to_csv(f, header=f.tell() == 0, index=False)


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


def get_rest_api_stats(github: GitHub, repo: dict):
    """Retrieves stats from the REST API for a repo, as
    the GraphQL API does not provide all stats"""

    repo_name = repo["name"]
    org_name = repo["owner"]["login"]

    ############################################################
    # Get webhooks count
    ############################################################
    response = github.rest.repos.list_webhooks(owner=org_name, repo=repo_name)
    repo["webhooks"] = {"totalCount": len(response.json())}

    ############################################################
    # Get workflows count
    ############################################################
    response = github.rest.actions.list_repo_workflows(org_name, repo_name)
    repo["workflows"] = {"totalCount": response.json()["total_count"]}

    ############################################################
    # Get last workflow run
    ############################################################
    response = github.rest.actions.list_workflow_runs_for_repo(org_name, repo_name)
    if response.json()["total_count"] == 0:
        repo["lastWorkflowRun"] = None
    else:
        repo["lastWorkflowRun"] = response.json()["workflow_runs"][0]["created_at"]

    ############################################################
    # Get repository topics
    ############################################################
    response = github.rest.repos.get_all_topics(org_name, repo_name)
    repo["topics"] = response.json()["names"]

    ############################################################
    # Check if GitLFS being used by checking .gitattributes
    ############################################################
    try:
        response = github.rest.repos.get_content(org_name, repo_name, ".gitattributes")

        # If .gitattributes contains the string '=lfs', then git LFS is enabled
        repo["hasGitLFS"] = "=lfs" in base64.b64decode(response.json()["content"])
    except Exception as e:
        repo["hasGitLFS"] = False
