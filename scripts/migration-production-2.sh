#!/bin/bash

##########################################
# Capture pre-migration source stats
##########################################

gh migrate stats --before --source


##########################################
# Migrate!
##########################################
gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccord \
    --github-target-org canaccord-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org finlogik \
    --github-target-org finlogik-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccorduk \
    --github-target-org canaccorduk-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose


##########################################
# Capture post-migration source stats
##########################################
gh migrate stats --after --source


##########################################
# Capture post-migration target stats
##########################################
gh migrate stats --after --target


##########################################
# Get migration logs
##########################################
gh migrate get logs


##########################################
# Generate post-migration report
##########################################
gh migrate report
