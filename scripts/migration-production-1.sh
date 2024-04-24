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
    --github-source-org canaccordci \
    --github-target-org canaccordci-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccordpartners \
    --github-target-org canaccordpartners-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org CanaccordQuestUK \
    --github-target-org CanaccordQuestUK-MIGRATE \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise target_slug \
    --github-source-org canaccordusa \
    --github-target-org canaccordusa-MIGRATE \
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
