#!/usr/bin/env bash

VERSION="1.2.1"
BIN_DIRECTORY=$(dirname $(which git))
BIN_PATH="$BIN_DIRECTORY/git-secrets"
DOWNLOAD_URL="https://raw.githubusercontent.com/awslabs/git-secrets/$VERSION/git-secrets"
ME=$(basename "$0")

echo "Checking git-secrets existence in PATH"
git secrets > /dev/null 2>&1
CALL_RESULT=$?

if [ "$CALL_RESULT" -ne "0" ]; then
    echo "Installing git-secrets v.$VERSION to $BIN_PATH from $DOWNLOAD_URL"
    wget $DOWNLOAD_URL -O $BIN_PATH
    RETCODE=$?
    if [ "$RETCODE" -ne "0" ]; then
        echo "Please run this script in privileged mode or install git-secrets v. $VERSION manually"
        echo "wget $DOWNLOAD_URL -O $BIN_PATH"
        echo "chmod a+x $BIN_PATH"
        exit 1
    fi
    chmod a+x $BIN_PATH
else
    REAL_PATH=$(which git-secrets)
    echo "git-secrets script already exists: $REAL_PATH"
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

echo "Allowing reset git hooks without privileged mode"
chmod a+rw .git/hooks/commit-msg
chmod a+rw .git/hooks/pre-commit
chmod a+rw .git/hooks/prepare-commit-msg

echo "Adding to post-checkout & post-merge hooks script invoking of $ME"
echo "#!/usr/bin/env bash" > .git/hooks/post-checkout
echo "bash $ME || true" >> .git/hooks/post-checkout
chmod a+rwx .git/hooks/post-checkout
echo "#!/usr/bin/env bash" > .git/hooks/post-merge
echo "bash $ME || true" >> .git/hooks/post-merge
chmod a+rwx .git/hooks/post-merge

if [ ! -z $USER ]; then
    echo "Thank you for using pre-commit hooks, $USER"
fi