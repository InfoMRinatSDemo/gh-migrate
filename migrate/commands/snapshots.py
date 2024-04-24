import click
import pandas as pd

import os
import base64
from functools import lru_cache
from githubkit import GitHub
from ..version import *

from migrate.workbook import get_included_orgs_by_wave


@click.command()
@click.option("--org", "orgs", multiple=True)
@click.option("--pat", "pat")
@click.option("--before", is_flag=True, help="Run before migration")
@click.option("--after", is_flag=True, help="Run after migration")
@click.option("--source", is_flag=True, help="Source organization(s)")
@click.option("--target", is_flag=True, help="Target organization(s)")
@click.option("--dry-run", is_flag=True, help="Is this a dry-run?")
@click.option("--wave", type=int, help="Wave number", required=True)
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="./report/InfoMagnus - Migration Workbook.xlsx",
)
@click.argument("output_dir", required=False, default="logs")
# @snapshot_before_after()
def snapshots(
    orgs, pat, before, after, source, target, dry_run, wave, workbook_path, output_dir
):
    ##########################################
    # Check command line fslags
    ##########################################
    if not (before ^ after):
        raise click.UsageError("You must supply either --before or --after")
    if not (source ^ target):
        raise click.UsageError("You must supply either --source or --target")

    ##########################################
    # Build output file name
    ##########################################
    if before and source:
        output_file = f"before-source-wave-{wave}.csv"
    elif before and target:
        output_file = f"before-target-wave-{wave}.csv"
    elif after and source:
        output_file = f"after-source-wave-{wave}.csv"
    elif after and target:
        output_file = f"after-target-wave-{wave}.csv"

    if dry_run:
        output_dir = os.path.join(output_dir, "dry-run")

    ##########################################
    # Get included source orgs from workbook
    ##########################################
    if orgs == ():
        if source:
            orgs = get_included_orgs_by_wave("source_name", wave, workbook_path)
        elif target:
            if dry_run:
                orgs = get_included_orgs_by_wave(
                    "dry_run_target_name", wave, workbook_path
                )
            else:
                orgs = get_included_orgs_by_wave("target_name", wave, workbook_path)

    ##########################################
    # Housekeeping
    ##########################################
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join("./", output_dir, output_file)

    # checkpoint_file(output_path, f"STATS: Saving old {output_path}")

    if os.path.exists(output_path):
        os.remove(output_path)

    ##########################################
    # The main event
    ##########################################
    print(f"* Inventorying {orgs}")

    if orgs is not None:
        for org in orgs:
            print(f"\n* Processing org {org}")
            github = GitHub(pat)
            if source:
                generate_snapshots("before", "source", org, pat)
            elif target:
                generate_snapshots("before", "target", org, pat)
            else:
                raise ValueError("Invalid source/target")

    # checkpoint_file(output_path, f"STATS: Saving new {output_path}")


##########################
# Generate snapshots
##########################
def generate_snapshots(timing, type, org_name, pat):
    """ """
    print(f"*** Generating {timing} {type} snapshots")
    github = GitHub(pat)

    def paginate(api_func, **kwargs):
        # See the githubkit README for more info about map_func
        pages = github.paginate(api_func, map_func=lambda r: r.json(), **kwargs)
        return pd.DataFrame([page for page in pages])

    def write_to_csv(dataframe, filename):
        output_dir = os.path.dirname(
            os.path.join("snapshots", timing, type, org_name, filename)
        )
        os.makedirs(output_dir, exist_ok=True)

        dataframe.to_csv(
            os.path.join(output_dir, os.path.basename(filename)), index=False
        )

    # Save all users in organization
    users = paginate(github.rest.orgs.list_members, org=org_name)
    write_to_csv(users, "users.csv")

    # Save all repos in organization
    repos = paginate(github.rest.repos.list_for_org, org=org_name)
    write_to_csv(repos, "repos.csv")

    # # Save all teams in organization
    teams = paginate(github.rest.teams.list, org=org_name)
    write_to_csv(teams, "teams.csv")

    all_team_repos = []
    all_team_users = []

    for team in teams.to_dict(orient="records"):
        team_slug = team["slug"]

        ############################
        # Save each team's repos
        ############################
        team_repos = paginate(
            github.rest.teams.list_repos_in_org,
            org=org_name,
            team_slug=team_slug,
        )
        # Add the team slug to the dataframe
        team_repos["team_slug"] = team_slug
        all_team_repos.append(team_repos)

        ############################
        # Save each team's users
        ############################
        team_users = paginate(
            github.rest.teams.list_members_in_org,
            org=org_name,
            team_slug=team_slug,
        )
        # Add the team slug to the dataframe
        team_users["team_slug"] = team_slug

        # Add each user's role to the dataframe
        for i, user in team_users.iterrows():
            response = github.rest.teams.get_membership_for_user_in_org(
                org=org_name, team_slug=team_slug, username=user["login"]
            )
            response = response.json()
            team_users.loc[i, "role"] = response["role"]

        all_team_users.append(team_users)

    all_team_repos = pd.concat(all_team_repos, ignore_index=True)
    all_team_users = pd.concat(all_team_users, ignore_index=True)

    # Move "team_slug" to the first column
    all_team_repos = all_team_repos[
        ["team_slug"] + [col for col in all_team_repos.columns if col != "team_slug"]
    ]

    # Move "team_slug" and "role" to the first columns
    all_team_users = all_team_users[
        ["team_slug", "role"]
        + [col for col in all_team_users.columns if col not in ["team_slug", "role"]]
    ]

    write_to_csv(all_team_repos, "team-repos.csv")
    write_to_csv(all_team_users, "team-users.csv")


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
    # Get branches
    ############################################################
    response = github.rest.repos.list_branches(org_name, repo_name)
    if len(response.json()) == 0:
        repo["branches"] = None
    else:
        repo["branches"] = [branch["name"] for branch in response.json()]
        repo["branches"].sort()

    ############################################################
    # Get teams
    ############################################################
    response = github.rest.repos.list_teams(org_name, repo_name)
    if len(response.json()) == 0:
        repo["teams"] = None
    else:
        repo["teams"] = [team["name"] for team in response.json()]
        repo["teams"].sort()

    ############################################################
    # Get environments
    ############################################################
    response = github.rest.repos.get_all_environments(org_name, repo_name)
    repo["environments"] = response.json()["total_count"]

    ############################################################
    # Get secrets
    ############################################################
    response = github.rest.actions.list_repo_secrets(org_name, repo_name)
    repo["secrets_actions_repo"] = response.json()["total_count"]

    response = github.rest.actions.list_repo_organization_secrets(org_name, repo_name)
    repo["secrets_actions_org"] = response.json()["total_count"]

    response = github.rest.dependabot.list_repo_secrets(org_name, repo_name)
    repo["secrets_dependabot"] = response.json()["total_count"]

    try:
        response = github.rest.codespaces.list_repo_secrets(org_name, repo_name)
        repo["secrets_codespaces"] = response.json()["total_count"]
    except:
        repo["secrets_codespaces"] = None

    ############################################################
    # Get repository topics, perms, visibility, security
    ############################################################
    response = github.rest.repos.get(org_name, repo_name)
    repo["topics"] = response.json()["topics"].sort()
    repo["permissions"] = response.json()["permissions"]
    repo["visibility"] = response.json()["visibility"]
    repo["security_and_analysis"] = response.json()["security_and_analysis"]

    ############################################################
    # Check if GitLFS being used by checking .gitattributes
    ############################################################
    try:
        response = github.rest.repos.get_content(org_name, repo_name, ".gitattributes")

        # If .gitattributes contains the string '=lfs', then git LFS is enabled
        repo["hasGitLFS"] = "=lfs" in base64.b64decode(response.json()["content"])
    except Exception as e:
        repo["hasGitLFS"] = False
