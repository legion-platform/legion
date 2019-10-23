*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}         legion/config_e2e_mlflow_wine
${WINE_ID}              test-e2e-wine

*** Settings ***
Documentation       Check wine model
Test Timeout        60 minutes
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Resource            ../../resources/keywords.robot
Library             Collections
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources
Suite Teardown      Run Keywords
...                 Cleanup resources  AND
...                 Remove file  ${LOCAL_CONFIG}
Force Tags          e2e  wine  edi

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose train delete --id ${WINE_ID} --ignore-not-found
    StrictShell  legionctl --verbose pack delete --id ${WINE_ID} --ignore-not-found
    StrictShell  legionctl --verbose dep delete --id ${WINE_ID} --ignore-not-found

*** Test Cases ***
Wine model
    StrictShell  legionctl --verbose train create -f ${RES_DIR}/wine/training.legion.yaml
    ${res}=  StrictShell  legionctl train get --id ${WINE_ID} -o 'jsonpath=$[0].status.artifacts[0].artifactName'

    StrictShell  legionctl --verbose pack create -f ${RES_DIR}/wine/packaging.legion.yaml --artifact-name ${res.stdout}
    ${res}=  StrictShell  legionctl pack get --id ${WINE_ID} -o 'jsonpath=$[0].status.results[0].value'

    StrictShell  legionctl --verbose dep create -f ${RES_DIR}/wine/deployment.legion.yaml --image ${res.stdout}

    Wait Until Keyword Succeeds  1m  0 sec  StrictShell  legionctl model info --mr ${WINE_ID}

    Wait Until Keyword Succeeds  1m  0 sec  StrictShell  legionctl model invoke --mr ${WINE_ID} --json-file ${RES_DIR}/wine/request.json

    ${res}=  Shell  legionctl model invoke --mr ${WINE_ID} --json-file ${RES_DIR}/wine/request.json --jwt wrong-token
    should not be equal  ${res.rc}  0

