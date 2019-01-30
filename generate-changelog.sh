#!/bin/bash

IMAGE=ferrarimarco/github-changelog-generator:1.14.3

if [[ -z "${CHANGELOG_GITHUB_TOKEN}" ]]; then
    echo "Please setup CHANGELOG_GITHUB_TOKEN env variable"
    echo "Link to generate: https://github.com/settings/tokens/new"
    exit 1
fi

if [[ -z "$1" ]]; then
    echo "Run this script with desired version, e.g. 0.10.0"
    exit 2
fi


docker run -it --rm \
           -v "$(pwd):/app" \
           -e "SRC_PATH=/app" \
           -w "/app" \
           -e "CHANGELOG_GITHUB_TOKEN=$CHANGELOG_GITHUB_TOKEN" \
           "$IMAGE" -u legion-platform -p legion --future-release $1
