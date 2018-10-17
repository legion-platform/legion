#!/usr/bin/env bash

VERSION="1.2.1"
BIN_DIRECTORY=$(dirname $(which git))
BIN_PATH="$BIN_DIRECTORY/git-secrets"
DOWNLOAD_URL="https://raw.githubusercontent.com/awslabs/git-secrets/$VERSION/git-secrets"
ME=$(basename "$0")

install_binaries()
{
    wget $DOWNLOAD_URL -O $BIN_PATH
    RETCODE=$?
    if [ "$RETCODE" -ne "0" ]; then
        echo "Please run this script in privileged mode or install git-secrets v. $VERSION manually"
        echo "wget $DOWNLOAD_URL -O $BIN_PATH"
        echo "chmod a+x $BIN_PATH"
        exit 1
    fi
    chmod a+x $BIN_PATH
}

install_hooks()
{
    echo "Checking git-secrets existence in PATH"
    git secrets > /dev/null 2>&1
    CALL_RESULT=$?

    if [ "$CALL_RESULT" -ne "0" ]; then
        echo "Install git secrets first"
        echo "To do in call (as priveleged user): $0 install_binaries"
        exit 1
    fi

    DIR=$(dirname "$(readlink "$0")")
    echo "Working in directory $DIR"

    echo "Flushing git-secrets configuration"
    git config --remove-section secrets || true

    cat "$DIR/.gitforbidden" | while read line
    do
        if [[ ! "$line" =~ ^#.* ]]; then
            echo "Adding forbidden regex pattern: $line"
            git secrets --add "$line"
        fi
    done

    cat "$DIR/.gitwhitelisted" | while read line
    do
        if [[ ! "$line" =~ ^#.* ]]; then
            echo "Adding allowed regex pattern: $line"
            git secrets --add -a "$line"
        fi
    done

    echo "Adding aws patterns"
    git secrets --register-aws

    echo "Registering hook"
    git secrets --install -f

    echo "Git secrets have been configured"
    echo "Configuration: "
    git secrets --list

    echo "Adding to post-checkout & post-merge hooks script invoking of $ME with argument install_hooks"
    echo "#!/usr/bin/env bash" > .git/hooks/post-checkout
    echo "bash $ME install_hooks || true" >> .git/hooks/post-checkout
    chmod a+x .git/hooks/post-checkout
    echo "#!/usr/bin/env bash" > .git/hooks/post-merge
    echo "bash $ME install_hooks || true" >> .git/hooks/post-merge
    chmod a+x .git/hooks/post-merge
}

if [ -z "$1" ]; then
    echo "Please run this script with required action."
    echo "Actions:"
    echo "$0 install_binaries -- to install git secrets binary in system. Should be runned in privileged mode"
    echo "$0 install_hooks -- to install git secrets hooks and actual regexpes"
else
    $1
fi