# InfoMagnus GitHub Migration Automator CLI

The IM GitHub Migration Automator is a GitHub CLI-based tool designed to help you plan and execute GitHub-to-GitHub migrations.

Specifically, the tool has been used to help plan and execute the StreamCo and CanacCord GHEC-to-GHEC EMU migrations.

## Overview

`gh migrate` consists of four commands:
- `gh migrate stats` -
- `gh migrate check` -
- `gh migrate diff` -
- `gh migrate plan` -

## Usage

During an engagement the tool is used as follows:

### Step 1: Generate source / target organization PATs

Personal Access Tokens (PATs) for both the source and target enterprise are
required to complete the "Pre-Migration Analysis".

The PATs must be of type "classic" with the following permissions: [link](images/pat-perms.png)

### Step 2: Discovery

In this step we generate inventories of the source enterprise:

```bash
gh migrate stats \
    --source-org source-org-1 \
    --source-org source-org-2 \
    --source-pat <source-org-PAT> \
    -o source-before-04-16-2024.csv
```

If the target enterprise is an existing, production environment, then it's important to generate an inventory of it.

This serves as a snapshot and baseline of the client's landscape prior to our engagement.  It is also useful in debugging, triaging, or even rolling-back an engagement.

```bash
gh migrate stats \
    --target-org target-org-1 \
    --target-org target-org-2 \
    --target-pat <target-org-PAT> \
    -o target-before-04-16-2024.csv
```

### Step 3: Dry-Run Planning

With the inventories gathered, we can begin planning the dry-run, and ultimately the production migration.

Use the `gh migrate plan` command to create the "migration workbook" which will be your sole data repository and planning tool to complete the migration.

```bash
gh migrate plan source-before-04-16-2024.csv
```

The initialized workbook is placed in `report/InfoMagnus - Migration Workbook.xlsx`.

#### Cover

The "Cover" sheet is where the engagement-specific details are entered....

![alt text](docs/images/workbook-cover.png)

#### Pre-migration Report

![alt text](docs/images/workbook-pre-migration-report.png)

The pre-migration report is used to identify potentially problematic repositories based on our past engagements.

There are typically:
- Repositories larger than 5GB

For more details see...

#### Mapping - Org

...

#### Inventory
...

### Step 4: Dry-Run Execution

Once you've identified which organizations will be part of the dry-run, you can generate the dry-run migration scripts:

```bash
gh migrate scripts dry-run "report/InfoMagnus - Migration Workbook.xlsx"
```

The dry-run script is placed in `scripts/dry-run.sh`, and looks like:

```bash
#!/bin/bash

##########################################
# Capture pre-migration source stats
##########################################
gh migrate stats \
    --source-org "org1" \
    --source-org "org2" \
    --source-pat secret! \
    -o before-source-dry-run-04-16-2024.csv

##########################################
# Migrate!
##########################################
gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org org1 \
    --github-target-org org1-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org org2 \
    --github-target-org org2-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

##########################################
# Capture post-migration source stats
##########################################
gh migrate stats \
    --source-org "org1" \
    --source-org "org2" \
    --source-pat secret! \
    -o after-source-dry-run-04-16-2024.csv

##########################################
# Capture post-migration target stats
##########################################
gh migrate stats \
    --target-org "org1-DRYRUN" \
    --target-org "org2-DRYRUN" \
    --target-pat omg! \
    -o after-target-dry-run-04-16-2024.csv
```

A dry-run is performed in four steps:
1. Capture a pre-migration snapshot of the source
2. Perform the migration
3. Capture a post-migration snapshot of the source
4. Capture a post-migration snapshot of the target

For more detail on the process see: [link](TBD)

### Step 5: Dry-Run Analysis

Analysis of the dry-run takes two steps:

1. Analysis of the source and target orgs using the `gh migrate diff` command:

    ```bash
    gh migrate diff \
        before-source-dry-run-04-16-2024.csv \
        after-source-dry-run-04-16-2024.csv \
        after-target-dry-run-04-16-2024.csv \
        "report/InfoMagnus - Migration Workbook.xlsx"
    ```

## Contributing
See [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## License
[Specify the license under which the tool is distributed]

## Contact
[Provide contact information for support or inquiries]
