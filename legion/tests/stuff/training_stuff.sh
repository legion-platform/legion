#!/usr/bin/env bash
set -e
set -o pipefail

MODEL_NAMES=(simple-model fail counter feedback)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TRAINED_ARTIFACTS_DIR="${DIR}/trained_artifacts"
LEGION_RESOURCES="${DIR}/legion_resources"
TEST_DATA="${DIR}/data"
COMMAND=setup

# Cleanups test model packaging from EDI server, cloud bucket and local filesystem.
# Arguments:
# $1 - Model packaging ID. It must be the same as the directory name where it locates.
function cleanup_pack_model() {
  local mp_id="${1}"

  # Removes the local zip file
  [ -f "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" ] && rm "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip"

  # Removes the test trained artifacts from bucket
  gsutil rm "gs://${CLUSTER_NAME}-data-store/output/${mp_id}.zip"

  # Removes the model packaging from EDI service
  legionctl --verbose pack delete --id "${mp_id}" --ignore-not-found
}

# Creates a "trained" artifact from a directory and copy it to the cloud bucket.
# After all, function starts the packaging process.
# Arguments:
# $1 - Model packaging ID. It must be the same as the directory name where it locates.
function pack_model() {
  local mp_id="${1}"

  [ -f "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" ] && rm "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip"

  # Creates trained zip artifact
  cd "${TRAINED_ARTIFACTS_DIR}/${mp_id}"
  zip -r "../${mp_id}.zip" -u ./
  cd -

  # Pushes trained zip artifact to the bucket
  gsutil cp "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" "gs://${CLUSTER_NAME}-data-store/output/${mp_id}.zip"
  rm "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip"

  # Repackages trained artifact to a docker image
  legionctl --verbose pack delete --id "${mp_id}" --ignore-not-found
  legionctl --verbose pack create --id "${mp_id}" --artifact-name "${mp_id}.zip" -f "${LEGION_RESOURCES}/packaging.legion.yaml"
}

# Waits for all background tasks.
# If one of a task fails, then function fails too.
function wait_all_background_task() {
  local fail_tasks=0

  for job in $(jobs -p); do
    echo "${job} waiting..."
    wait "${job}" || ((fail_tasks + 1))
  done

  if [[ "$fail_tasks" != "0" ]]; then
    echo "Failed $fail_tasks linters"
    exit 1
  fi
}

# Main entrypoint for setup command.
# The function creates the model packaings and the toolchain integrations.
function setup() {
  for mp_id in "${MODEL_NAMES[@]}"; do
    pack_model "${mp_id}" &
  done

  # Create training-data-helper toolchain integration
  jq ".spec.defaultImage = \"${DOCKER_REGISTRY}/legion-pipeline-agent:${LEGION_VERSION}\"" "${LEGION_RESOURCES}/template.training_data_helper_ti.json" >"${LEGION_RESOURCES}/training_data_helper_ti.json"
  legionctl ti delete -f "${LEGION_RESOURCES}/training_data_helper_ti.json" --ignore-not-found
  legionctl ti create -f "${LEGION_RESOURCES}/training_data_helper_ti.json"
  rm "${LEGION_RESOURCES}/training_data_helper_ti.json"

  # Pushes a test data to the bucket
  gsutil cp -r "${TEST_DATA}/" "gs://${CLUSTER_NAME}-data-store/test-data/"

  wait_all_background_task
}

# Main entrypoint for cleanup command.
# The function deletes the model packaings and the toolchain integrations.
function cleanup() {
  for mp_id in "${MODEL_NAMES[@]}"; do
    cleanup_pack_model "${mp_id}" &
  done

  legionctl ti delete -f "${LEGION_RESOURCES}/training_data_helper_ti.yaml" --ignore-not-found

  # Cleanup a test data in the bucket
  gsutil rm "gs://${CLUSTER_NAME}-data-store/test-data"
}

# Prints the help message
function usage() {
  echo "Setup or cleanup training stuff for robot tests."
  echo "usage: training_stuff.sh [[setup|cleanup][--models][--help][--verbose]"
}

# The command line arguments parsing
while [ "${1}" != "" ]; do
  case "${1}" in
  setup)
    shift
    COMMAND=setup
    ;;
  cleanup)
    shift
    COMMAND=cleanup
    ;;
  --models)
    mapfile -t MODEL_NAMES <<< "${2}"
    shift
    shift
    ;;
  --verbose)
    set -x
    shift
    ;;
  --help)
    usage
    exit
    ;;
  *)
    usage
    exit 1
    ;;
  esac
done

# Main programm entrypoint
case "${COMMAND}" in
setup)
  setup
  ;;
cleanup)
  cleanup
  ;;
*)
  echo "Unxpected command: ${COMMAND}"
  usage
  exit 1
  ;;
esac

