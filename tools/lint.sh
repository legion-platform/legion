#!/bin/bash
set -e

PYLINT_FOLDER="target/pylint"
PYDOCSTYLE_FOLDER="target/pydocstyle"

legion_pylint="sdk cli services toolchains/python tests/unit tests/e2e/python"
projects_pydocstyle="sdk cli services toolchains/python"

# Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
touch legion/tests/unit/__init__.py legion/tests/e2e/python/__init__.py
trap "rm legion/tests/unit/__init__.py legion/tests/e2e/python/__init__.py" SIGINT SIGTERM SIGHUP SIGQUIT EXIT ERR

rm -rf "${PYLINT_FOLDER}"
mkdir -p "${PYLINT_FOLDER}"
mkdir -p "${PYLINT_FOLDER}/legion-toolchains"

for service in $legion_pylint
do
    pylint --output-format=parseable --reports=no "legion/${service}/legion" > "${PYLINT_FOLDER}/legion-${service}.log" &
done

rm -rf "${PYDOCSTYLE_FOLDER}"
mkdir -p "${PYDOCSTYLE_FOLDER}"
mkdir -p "${PYDOCSTYLE_FOLDER}/legion-toolchains"
for service in $projects_pydocstyle
do
    pydocstyle --source "legion/${service}/legion" > "${PYDOCSTYLE_FOLDER}/legion-${service}.log" &
done

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