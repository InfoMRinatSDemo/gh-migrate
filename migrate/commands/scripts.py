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
    template = env.get_template(os.path.join("scripts", "templates", template_name))

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

    # checkpoint_file(workbook_path, f"SCRIPTS: Saving old {workbook_path}")

    if dry_run:
        print(f"\n* Generating dry-run migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("dry_run_target_name", wave, workbook_path)
    else:
        print(f"\n* Generating production migration script for wave: {wave}")
        orgs = get_included_orgs_by_wave_df("target_name", wave, workbook_path)

    # Get the number of unique waves
    waves = orgs["wave"].unique()

    # Create a migration script for each wave
    for wave in waves:
        # Get the orgs for this wave
        wave_orgs = orgs[orgs["wave"] == wave].to_dict(orient="records")

        if dry_run:
            # checkpoint_file("./scripts/dry-run.sh", f"SCRIPTS: Saving old dry-run.sh")
            render_template(
                "migration.sh.j2",
                f"migration-dry-run-{wave}.sh",
                target_slug="target_slug",
                orgs=wave_orgs,
                dry_run=True,
                wave=wave,
            )

        else:
            # checkpoint_file("./scripts/migration.sh", f"SCRIPTS: Saving old migration.sh")
            render_template(
                "migration.sh.j2",
                f"migration-production-{wave}.sh",
                target_slug="target_slug",
                orgs=wave_orgs,
                dry_run=False,
                wave=wave,
            )

    # checkpoint_file("./scripts/migration.sh", f"SCRIPTS: Saving new migration.sh")


###############################
# Create teams
###############################
@scripts.command()
def create_teams(teams):
    """
    Generate the "create teams" script.
    """
    render_template("step5-create-teams.sh.j2", teams=teams)


###############################
# Update team permissions
###############################
@scripts.command()
def update_team_perms():
    """
    Generate the "update team permissions" script.
    """
    # Read in each of the source org's team-repos csv files
    team_repos_dir = os.path.join(
        SNAPSHOTS_DIR, "initial", "source", SOURCE_ORG, "team-repos"
    )

    # Combine contents of all csv files into a single dataframe
    team_repos_df = pd.concat(
        [pd.read_csv(f) for f in glob.glob(os.path.join(team_repos_dir, "*.csv"))],
        ignore_index=True,
    )

    render_template(
        "step5-update-team-perms.sh.j2",
        repos=team_repos_df.to_dict(orient="records"),
    )


###############################
# Add users to teams
###############################
@scripts.command()
def add_users_to_teams():
    """
    Generate the "add users to teams" script.
    """
    # Read in each of the source org's team-users csv files
    team_users_dir = os.path.join(
        SNAPSHOTS_DIR, "initial", "source", SOURCE_ORG, "team-users"
    )

    # Combine contents of all csv files into a single dataframe
    team_users_df = pd.concat(
        [pd.read_csv(f) for f in glob.glob(os.path.join(team_users_dir, "*.csv"))],
        ignore_index=True,
    )

    # The mannequins file contains the mapping of mannequin-user to target-user
    mannequins_df = pd.read_csv(os.path.join(MAPPINGS_DIR, "mannequins.csv"))

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
        print(f"*** Couldn't map these users:")
        print(unmapped_users[["team_slug", "login", "mannequin-user", "target-user"]])

    mapped_users = mapped_users[mapped_users["target-user"].notna()]
    render_template(
        "step5-add-users-to-teams.sh.j2",
        users=mapped_users.to_dict(orient="records"),
    )


###############################
# Get migration logs
###############################
@scripts.command()
def get_migration_logs(repos):
    """
    Generate the "get migration logs" script.
    """
    render_template("step5-get-migration-logs.sh.j2", repos=repos)


###############################
# Rollback migration
###############################
@scripts.command()
def rollback_migration(repos):
    """
    Generate the "rollback migration" script.
    """
    render_template("step5-rollback-migration.sh.j2", repos=repos)
