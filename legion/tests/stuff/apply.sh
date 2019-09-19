#!/usr/bin/env bash
set -e

MODEL_NAME=(simple-model fail counter feedback)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function pack_model() {
    md_name=${1}
    [ -f "${DIR}/${md_name}.zip" ] && rm "${DIR}/${md_name}.zip"
    cd "${DIR}/${md_name}"
    zip -r "../${md_name}.zip" -u ./
    cd -

    gsutil cp "${DIR}/${md_name}.zip" "gs://${CLUSTER_NAME}-data-store/output/${md_name}.zip"
    rm "${DIR}/${md_name}.zip"

    legionctl --verbose pack delete --id "${md_name}" --ignore-not-found
    legionctl --verbose pack create --id "${md_name}" --artifact-name "${md_name}.zip" -f "${DIR}/packaging.legion.yaml"
}

for md_name in ${MODEL_NAME[@]}
do
  pack_model "${md_name}" &
done

FAIL=0
# Wait all background linters
for job in $(jobs -p)
do
    echo "${job} waiting..."
    wait "${job}" || ((FAIL + 1))
done

if [[ "$FAIL" != "0" ]];
then
    echo "Failed $FAIL linters"
    exit 1
fi
