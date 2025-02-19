#!/bin/bash

##########################################
# Capture pre-migration source stats
##########################################
gh migrate stats \
    --source-org "canaccordci" \
    --source-org "canaccordpartners" \
    --source-org "CanaccordQuestUK" \
    --source-org "canaccordusa" \
    --source-org "canaccord" \
    --source-org "finlogik" \
    --source-org "canaccorduk" \
    --source-pat secret! \
    -o before-source-dry-run-04-16-2024.csv

##########################################
# Migrate!
##########################################
gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org canaccordci \
    --github-target-org canaccordci-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org canaccordpartners \
    --github-target-org canaccordpartners-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org CanaccordQuestUK \
    --github-target-org CanaccordQuestUK-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org canaccordusa \
    --github-target-org canaccordusa-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org canaccord \
    --github-target-org canaccord-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org finlogik \
    --github-target-org finlogik-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose

gh gei migrate-org \
    --github-target-enterprise  \
    --github-source-org canaccorduk \
    --github-target-org canaccorduk-DRYRUN \
    --github-source-pat secret! \
    --github-target-pat omg! \
    --verbose
##########################################
# Capture post-migration source stats
##########################################
gh migrate stats \
    --source-org "canaccordci" \
    --source-org "canaccordpartners" \
    --source-org "CanaccordQuestUK" \
    --source-org "canaccordusa" \
    --source-org "canaccord" \
    --source-org "finlogik" \
    --source-org "canaccorduk" \
    --source-pat secret! \
    -o after-source-dry-run-04-16-2024.csv

##########################################
# Capture post-migration target stats
##########################################
gh migrate stats \
    --target-org "canaccordci-DRYRUN" \
    --target-org "canaccordpartners-DRYRUN" \
    --target-org "CanaccordQuestUK-DRYRUN" \
    --target-org "canaccordusa-DRYRUN" \
    --target-org "canaccord-DRYRUN" \
    --target-org "finlogik-DRYRUN" \
    --target-org "canaccorduk-DRYRUN" \
    --target-pat omg! \
    -o after-target-dry-run-04-16-2024.csv

##########################################
# Capture migration logs
##########################################
gh migrate check \
    --target-org "canaccordci" \
    --target-org "canaccordpartners" \
    --target-org "CanaccordQuestUK" \
    --target-org "canaccordusa" \
    --target-org "canaccord" \
    --target-org "finlogik" \
    --target-org "canaccorduk" \
    --target-pat omg! \
    -o logs