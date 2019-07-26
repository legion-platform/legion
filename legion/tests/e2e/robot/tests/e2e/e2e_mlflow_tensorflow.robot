*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}         legion/config_e2e_mlflow_tensorflow
${TENSORFLOW_ID}        test-e2e-tensorflow

*** Settings ***
Documentation       Check tensorflow model
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Resource            ../../resources/keywords.robot
Library             Collections
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources
Suite Teardown      Cleanup resources
Force Tags          e2e  tensorflow  edi

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose train delete --id ${TENSORFLOW_ID} --ignore-not-found
    StrictShell  legionctl --verbose pack delete --id ${TENSORFLOW_ID} --ignore-not-found
    StrictShell  legionctl --verbose dep delete --id ${TENSORFLOW_ID} --ignore-not-found

*** Test Cases ***
Tensorflow model
    StrictShell  legionctl --verbose train create -f ${RES_DIR}/tensorflow/training.legion.yaml
    ${res}=  StrictShell  legionctl train get --id ${TENSORFLOW_ID} -o 'jsonpath=$[0].status.artifacts[0].artifactName'

    StrictShell  legionctl --verbose pack create -f ${RES_DIR}/tensorflow/packaging.legion.yaml --artifact-name ${res.stdout}
    ${res}=  StrictShell  legionctl pack get --id ${TENSORFLOW_ID} -o 'jsonpath=$[0].status.results[0].value'

    StrictShell  legionctl --verbose dep create -f ${RES_DIR}/tensorflow/deployment.legion.yaml --image ${res.stdout}

    StrictShell  legionctl dep generate-token --md-id ${TENSORFLOW_ID}

    StrictShell  legionctl --verbose model info --mr ${TENSORFLOW_ID}

    StrictShell  legionctl --verbose model invoke --mr ${TENSORFLOW_ID} --json-file ${RES_DIR}/tensorflow/request.json

    ${res}=  Shell  legionctl model invoke --mr ${TENSORFLOW_ID} --json-file ${RES_DIR}/tensorflow/request.json --jwt wrong-token
    should not be equal  ${res.rc}  0
