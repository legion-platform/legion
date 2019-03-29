#!/bin/bash
set -e

PYLINT_FOLDER="target/pylint"
PYDOCSTYLE_FOLDER="target/pydocstyle"

# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
touch legion/tests/unit/__init__.py legion/tests/e2e/python/__init__.py
trap "rm legion/tests/unit/__init__.py legion/tests/e2e/python/__init__.py" SIGINT SIGTERM SIGHUP SIGQUIT EXIT ERR

function pylint_cmd() {
    package_dir="${1}"
    output_name="${2}"

    pylint --output-format=parseable --reports=no "legion/${package_dir}" 2>&1 | tee "${PYLINT_FOLDER}/legion-${output_name}.log" &
}

rm -rf "${PYLINT_FOLDER}"
mkdir -p "${PYLINT_FOLDER}"

pylint_cmd sdk/legion sdk
pylint_cmd cli/legion cli
pylint_cmd robot/legion robot
pylint_cmd services/legion services
pylint_cmd toolchains/python/legion toolchain
pylint_cmd tests/unit unit
pylint_cmd tests/e2e/python e2e

function pydocstyle_cmd() {
    package_dir="${1}"
    output_name="${2}"

    pydocstyle --source "legion/${package_dir}" 2>&1 | tee "${PYDOCSTYLE_FOLDER}/legion-${output_name}.log" &
}

rm -rf "${PYDOCSTYLE_FOLDER}"
mkdir -p "${PYDOCSTYLE_FOLDER}"

pydocstyle_cmd sdk/legion sdk
pydocstyle_cmd cli/legion cli
pydocstyle_cmd robot/legion robot
pydocstyle_cmd services/legion services
pydocstyle_cmd toolchains/python/legion toolchain

FAIL=0
# Wait all background linters
for job in `jobs -p`
do
echo $job
    echo "waiting..."
    wait $job || let "FAIL+=1"
done

cat ${PYLINT_FOLDER}/*.log > "${PYLINT_FOLDER}/legion.log"
cat ${PYDOCSTYLE_FOLDER}/*.log > "${PYDOCSTYLE_FOLDER}/legion.log"

cat "${PYDOCSTYLE_FOLDER}/legion.log"
cat "${PYLINT_FOLDER}/legion.log"
echo "You can find the result of linting here: ${PYLINT_FOLDER} and ${PYDOCSTYLE_FOLDER}"

if [[ "$FAIL" != "0" ]];
then
    echo "Failed $FAIL linters"
    exit 1
fi