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

The `gh migrate plan` command to create the "migration workbook", which serves as the data repository and planning tool for the rest of the migration.

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

#### Inventory
...

### Step 4: Dry-Run Execution



## Features
- [List the key features and functionalities of the tool]

## Installation
1. [Provide step-by-step instructions on how to install the tool]
2. [Include any dependencies or prerequisites]

## Usage
1. [Explain how to use the tool]
2. [Include examples or code snippets if applicable]

## Contributing
- [Explain how others can contribute to the development of the tool]
- [Include guidelines for submitting pull requests or raising issues]

## License
[Specify the license under which the tool is distributed]

## Contact
[Provide contact information for support or inquiries]
