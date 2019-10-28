#!/usr/bin/env bash
set -e
set -o pipefail

MODEL_NAMES=(simple-model fail counter feedback)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TRAINED_ARTIFACTS_DIR="${DIR}/trained_artifacts"
LEGION_RESOURCES="${DIR}/legion_resources"
TEST_DATA="${DIR}/data"
COMMAND=setup
# Test connection points to the test data directory
TEST_DATA_DIR_CONNECTION_ID=test-data-dir
# Test connection points to the test data file
TEST_DATA_FILE_CONNECTION_ID=test-data-file
TEST_DATA_TI_ID=training-data-helper

# Cleanups test model packaging from EDI server, cloud bucket and local filesystem.
# Arguments:
# $1 - Model packaging ID. It must be the same as the directory name where it locates.
function cleanup_pack_model() {
  local mp_id="${1}"

  # Removes the local zip file
  [ -f "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" ] && rm "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip"

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
  case "${CLOUD_PROVIDER}" in
  aws)
    aws s3 cp "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" "s3://${CLUSTER_NAME}-data-store/output/${mp_id}.zip"
    ;;
  azure)
    STORAGE_ACCOUNT=$(az storage account list -g "${CLUSTER_NAME}" --query "[?tags.cluster=='${CLUSTER_NAME}' && tags.purpose=='Legion models storage'].[name]" -otsv)
    az storage blob upload --account-name "${STORAGE_ACCOUNT}" -c "${CLUSTER_NAME}-data-store" \
      -f "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" -n "output/${mp_id}.zip"
    ;;
  gcp)
    gsutil cp "${TRAINED_ARTIFACTS_DIR}/${mp_id}.zip" "gs://${CLUSTER_NAME}-data-store/output/${mp_id}.zip"
    ;;
  *)
    echo "Unexpected CLOUD_PROVIDER: ${CLOUD_PROVIDER}"
    usage
    exit 1
    ;;
  esac

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
    wait "${job}" || ((fail_tasks = fail_tasks + 1))
  done

  if [[ "$fail_tasks" -ne "0" ]]; then
    echo "Failed $fail_tasks linters"
    exit 1
  fi
}

# Create a test data Legion connection based on models-output connection.
# Arguments:
# $1 - Legion connection ID, which will be used for new connection
# $2 - Legion connection uri, which will be used for new connection
function create_test_data_connection() {
  local conn_id="${1}"
  local conn_uri="${2}"
  local conn_file="test-data-connection.yaml"

  # Replaced the uri with the test data directory and added the kind field
  legionctl conn get --id models-output -o json |
    conn_uri="${conn_uri}" jq '.[0].spec.uri = env.conn_uri | .[] | .kind = "Connection"' \
      >"${conn_file}"

  legionctl conn delete --id "${conn_id}" --ignore-not-found
  legionctl conn create -f "${conn_file}" --id "${conn_id}"
  rm "${conn_file}"
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

  # Pushes a test data to the bucket and create a file with the connection
  case "${CLOUD_PROVIDER}" in
  aws)
    remote_dir="s3://${CLUSTER_NAME}-data-store/test-data"

    aws s3 cp --recursive "${TEST_DATA}/" "${remote_dir}/data/"
    ;;
  azure)
    remote_dir="${CLUSTER_NAME}-data-store/test-data"
    STORAGE_ACCOUNT=$(az storage account list -g "${CLUSTER_NAME}" --query "[?tags.cluster=='${CLUSTER_NAME}' && tags.purpose=='Legion models storage'].[name]" -otsv)

    az storage blob upload-batch --account-name "${STORAGE_ACCOUNT}" --source "${TEST_DATA}/" \
      --destination "${CLUSTER_NAME}-data-store" --destination-path "test-data/data"
    ;;
  gcp)
    remote_dir="gs://${CLUSTER_NAME}-data-store/test-data"

    gsutil cp -r "${TEST_DATA}/" "${remote_dir}/"
    ;;
  *)
    echo "Unexpected CLOUD_PROVIDER: ${CLOUD_PROVIDER}"
    usage
    exit 1
    ;;
  esac

  # Update test-data connections
  create_test_data_connection "${TEST_DATA_FILE_CONNECTION_ID}" "${remote_dir}/data/legion.project.yaml"
  create_test_data_connection "${TEST_DATA_DIR_CONNECTION_ID}" "${remote_dir}/data/"

  wait_all_background_task
}

# Main entrypoint for cleanup command.
# The function deletes the model packaings and the toolchain integrations.
function cleanup() {
  for mp_id in "${MODEL_NAMES[@]}"; do
    cleanup_pack_model "${mp_id}" &
  done

  legionctl ti delete --id ${TEST_DATA_TI_ID} --ignore-not-found
  legionctl conn delete --id ${TEST_DATA_DIR_CONNECTION_ID} --ignore-not-found
  legionctl conn delete --id ${TEST_DATA_FILE_CONNECTION_ID} --ignore-not-found
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
    mapfile -t MODEL_NAMES <<<"${2}"
    shift 2
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
