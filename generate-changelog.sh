#!/bin/bash

docker run -it --rm -v "$(pwd):/app" -e "SRC_PATH=/app" -w "/app"  -e "CHANGELOG_GITHUB_TOKEN=$CHANGELOG_GITHUB_TOKEN" ferrarimarco/github-changelog-generator:1.14.3 legion-platform/legion