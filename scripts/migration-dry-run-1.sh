#!/bin/bash

source .env.pats

##########################################
# Capture pre-migration source stats
##########################################

gh migrate stats --before --source --dry-run --wave 1


##########################################
# Migrate!
##########################################
gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccordci \
    --github-target-org canaccordci-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccordpartners \
    --github-target-org canaccordpartners-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org CanaccordQuestUK \
    --github-target-org CanaccordQuestUK-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccordusa \
    --github-target-org canaccordusa-DRYRUN \
    --github-source-pat source_pat \
    --github-target-pat target_pat \
    --verbose


##########################################
# Capture post-migration source stats
##########################################
gh migrate stats --after --source --dry-run --wave 1

##########################################
# Capture post-migration target stats
##########################################
gh migrate stats --after --target --dry-run --wave 1

##########################################
# Get migration logs
##########################################
gh migrate get logs --dry-run --wave 1

##########################################
# Generate post-migration report
##########################################
gh migrate report --dry-run --wave 1