import glob
import os
import click
from jinja2 import Environment, FileSystemLoader
import pandas as pd

from ..workbook import *
from migrate.version import checkpoint_file


@click.group()
def scripts():
    pass


def render_template(template_name, output_name, **kwargs):
    """
    Render a jinja2 template and write it to a file.
    """
    env = Environment(loader=FileSystemLoader("."))

    # TODO: Figure out why the first line doesn't work
    # template = env.get_template(os.path.join("scripts", "templates", template_name))
    template = env.get_template(f"./scripts/templates/{template_name}")

    # Render the template with the data
    output = template.render(source_pat="source_pat", target_pat="target_pat", **kwargs)

    # Remove .j2 from the template name
    # script_name = template_name.replace(".j2", "")

    # Write the rendered migration script to the file
    with open(os.path.join("scripts", output_name), "w") as f:
        f.write(output)


###############################
# Migration script
###############################
@scripts.command()
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="./report/InfoMagnus - Migration Workbook.xlsx",
)
@click.option("--dry-run", is_flag=True, help="Is this a dry-run?")
@click.option("--wave", type=int, help="Wave number", required=True)
def migration(workbook_path, dry_run, wave):
    """
    Generate the migration script.
    """

    if dry_run:
        print(f"\n* Generating dry-run migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("dry_run_target_name", wave, workbook_path)
    else:
        print(f"\n* Generating production migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("target_name", wave, workbook_path)

    # Get the orgs for this wave
    wave_orgs = orgs[orgs["wave"] == wave].to_dict(orient="records")

    if dry_run:
        render_template(
            "migration.sh.j2",
            f"wave-{wave}-migration-dry-run.sh",
            target_slug="target_slug",
            orgs=wave_orgs,
            dry_run=True,
            wave=wave,
        )

    else:
        render_template(
            "migration.sh.j2",
            f"wave-{wave}-migration-production.sh",
            target_slug="target_slug",
            orgs=wave_orgs,
            dry_run=False,
            wave=wave,
        )


##############################################################################
# Post-migration scripts
##############################################################################
@scripts.command()
@click.option(
    "-w",
    "--workbook",
    "workbook_path",
    required=False,
    default="./report/InfoMagnus - Migration Workbook.xlsx",
)
@click.option("--dry-run", is_flag=True, help="Is this a dry-run?")
@click.option("--wave", type=int, help="Wave number", required=True)
def post_migration(workbook_path, dry_run, wave):
    print("*** Generating post-migration scripts")

    if dry_run:
        print(f"* Generating dry-run post-migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("dry_run_target_name", wave, workbook_path)
        prefix = "DRY-RUN"
    else:
        print(f"* Generating production post-migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("target_name", wave, workbook_path)
        prefix = "PRODUCTION"

    ###############################
    # Create post-migration scripts
    ###############################

    # Get the orgs for this wave
    wave_orgs = orgs[orgs["wave"] == wave].to_dict(orient="records")

    for org in wave_orgs:
        source_org = org["source_name"]
        target_org = org["target_name"]

        ###############################
        # Update team permissions
        ###############################
        team_repos_dir = os.path.join(
            "snapshots", "before", "source", source_org, "team-repos.csv"
        )

        team_repos_df = pd.read_csv(team_repos_dir)

        output_file = f"{prefix}-wave-{int(wave)}-update-team-perms-{target_org}.sh"

        render_template(
            "update-team-perms.sh.j2",
            output_file,
            repos=team_repos_df.to_dict(orient="records"),
            target_org=target_org,
        )

        ###############################
        # Add users to teams
        ###############################
        team_users_file = os.path.join(
            "snapshots", "before", "source", source_org, "team-users.csv"
        )

        team_users_df = pd.read_csv(team_users_file)

        # The mannequins file contains the mapping of mannequin-user to target-user
        mannequins_df = get_mannequin_df(workbook_path)

        # Map the user from the source org to target org using mannequins.csv
        mapped_users = team_users_df.merge(
            # We use a left join so we can identify unmapped users
            # (they will be NaN in the "target-user" column)
            mannequins_df,
            how="left",
            left_on="login",
            right_on="mannequin-user",
        )

        # Identify unmapped users
        unmapped_users = mapped_users[mapped_users["target-user"].isna()]
        if not unmapped_users.empty:
            print(f"*** Couldn't map these users for {target_org}:")
            print(
                unmapped_users[["team_slug", "login", "mannequin-user", "target-user"]]
            )

        output_file = f"{prefix}-wave-{int(wave)}-add-users-to-teams-{target_org}.sh"

        mapped_users = mapped_users[mapped_users["target-user"].notna()]
        render_template(
            "add-users-to-teams.sh.j2",
            output_file,
            users=mapped_users.to_dict(orient="records"),
            target_org=target_org,
        )

    # repos = get_repos_by_exclude("exclude")
    # teams = get_teams_by_exclude("exclude")


# ###############################
# # Create teams
# ###############################
# @scripts.command()
# def create_teams(teams):
#     """
#     Generate the "create teams" script.
#     """
#     render_template("step5-create-teams.sh.j2", teams=teams)


# ###############################
# # Get migration logs
# ###############################
# @scripts.command()
# def get_migration_logs(repos):
#     """
#     Generate the "get migration logs" script.
#     """
#     render_template("step5-get-migration-logs.sh.j2", repos=repos)


# ###############################
# # Rollback migration
# ###############################
# @scripts.command()
# def rollback_migration(repos):
#     """
#     Generate the "rollback migration" script.
#     """
#     render_template("step5-rollback-migration.sh.j2", repos=repos)
