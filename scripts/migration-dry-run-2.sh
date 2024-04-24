#!/bin/bash

source .env.pats

##########################################
# Capture pre-migration source stats
##########################################

gh migrate stats --before --source --dry-run --wave 2


##########################################
# Migrate!
##########################################
gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccord \
    --github-target-org canaccord-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org finlogik \
    --github-target-org finlogik-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccorduk \
    --github-target-org canaccorduk-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose


##########################################
# Capture post-migration source stats
##########################################
gh migrate stats --after --source --dry-run --wave 2

##########################################
# Capture post-migration target stats
##########################################
gh migrate stats --after --target --dry-run --wave 2

##########################################
# Get migration logs
##########################################
gh migrate get logs --dry-run --wave 2

##########################################
# Generate post-migration report
##########################################
gh migrate report --dry-run --wave 2