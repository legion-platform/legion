*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}        legion/config_deployment_cli
${MD_SIMPLE_MODEL}     simple-model-cli

*** Settings ***
Documentation       Legion's EDI operational check for operations on ModelDeployment resources
Test Timeout        20 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Force Tags          deployment  edi  cli
Suite Setup         Run Keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose dep delete --id ${MD_SIMPLE_MODEL} --ignore-not-found

*** Test Cases ***
Undeploy. Nonexistent model service
    [Documentation]  The undeploy command must fail if a model cannot be found by name
    ${res}=  Shell  legionctl --verbose dep delete --id this-model-does-not-exsit
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  not found

Deploy. Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    ${res}=  Shell  legionctl --verbose dep create -f ${RES_DIR}/custom-resources.deployment.legion.yaml --timeout=0
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  must be positive integer

Deploy. Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    ${res}=  Shell  legionctl --verbose dep create -f ${RES_DIR}/custom-resources.deployment.legion.yaml --timeout=-500
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  must be positive integer

Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose dep --token "${AUTH_TOKEN}" get
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Can not reach http://localhost:5000

Wrong token
    [Documentation]  The inspect command must fail if it does not contain a token
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose dep --edi ${EDI_URL} --token wrong-token get
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Login. Override login values
    [Documentation]  Command line parameters must be overrided by config parameters
    [Teardown]  Login to the edi and edge
    [Setup]     Remove File  ${LOCAL_CONFIG}
    ${res}=  Shell  legionctl --verbose login --edi ${EDI_URL} --token "${AUTH_TOKEN}"
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose dep --edi ${EDI_URL} --token wrong-token get
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Credentials are not correct

Deploy fails when validation fails
    [Documentation]  Deploy fails when memory resource is incorect
    ${res}=  Shell  legionctl --verbose dep create -f ${RES_DIR}/validation-fail.deployment.legion.yaml
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  minimum number of replicas parameter must not be less than maximum number of replicas parameter
