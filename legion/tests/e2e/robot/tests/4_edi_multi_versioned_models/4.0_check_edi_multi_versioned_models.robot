*** Variables ***
${LOCAL_CONFIG}  legion/config_4_0
${TEST_MODEL_NAME}       4
${TEST_MODEL_VERSION_1}  1
${TEST_MODEL_VERSION_2}  2
${TEST_MT_NAME_1}     stub-model-4-1
${TEST_MT_NAME_2}     stub-model-4-2
${TEST_MD_NAME_1}     stub-model-4-1
${TEST_MD_NAME_2}     stub-model-4-2

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.grafana.Grafana
Library             legion.robot.libraries.model.Model
Library             Collections
Suite Setup         Run keywords  Choose cluster context    ${CLUSTER_CONTEXT}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build model  ${TEST_MT_NAME_1}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_1}  \${TEST_MODEL_IMAGE_1}  AND
...                 Build model  ${TEST_MT_NAME_2}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_2}  \${TEST_MODEL_IMAGE_2}  AND
...                 Get token from EDI  ${TEST_MD_NAME_1}  ${TEST_MD_NAME_1}  AND
...                 Get token from EDI  ${TEST_MD_NAME_2}  ${TEST_MD_NAME_2}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_1}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_2}
Suite Teardown      Run keywords  Delete model training  ${TEST_MT_NAME_1}  AND
...                 Delete model training  ${TEST_MT_NAME_2}  AND
...                 Remove File  ${LOCAL_CONFIG}
Test Setup          Run Keywords
...                 Run EDI deploy and check model started  ${TEST_MD_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_1}  ${TEST_MD_NAME_1}  AND
...                 Run EDI deploy and check model started  ${TEST_MD_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_2}  ${TEST_MD_NAME_2}
Test Teardown       Run Keywords
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_1}    AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME_2}
Force Tags          edi  cli  enclave  multi_versions

*** Test Cases ***
Check EDI deploy 2 models with different versions but the same name
    [Setup]         NONE
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MD_NAME_1} --image ${TEST_MODEL_IMAGE_1} --role ${TEST_MD_NAME_1}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Wait Until Keyword Succeeds  1m  0 sec  Check model started  ${TEST_MD_NAME_1}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_1}'
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MD_NAME_2} --image ${TEST_MODEL_IMAGE_2} --role ${TEST_MD_NAME_2}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Wait Until Keyword Succeeds  1m  0 sec  Check model started  ${TEST_MD_NAME_2}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_2}'

Check EDI deploy 2 models with the same image
    [Setup]         NONE
    [Tags]  apps
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MD_NAME_1} --image ${TEST_MODEL_IMAGE_1} --role ${TEST_MD_NAME_1}
                    Should Be Equal     ${resp.rc}         ${0}
    ${resp}=        Shell  legionctl --verbose md create ${TEST_MD_NAME_2} --image ${TEST_MODEL_IMAGE_2} --role ${TEST_MD_NAME_2}
                    Should Be Equal     ${resp.rc}         ${0}

    ${resp}=        Wait Until Keyword Succeeds  1m  0 sec  Check model started  ${TEST_MD_NAME_1}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_1}'
    ${resp}=        Wait Until Keyword Succeeds  1m  0 sec  Check model started  ${TEST_MD_NAME_2}
                    Should contain                  ${resp}                 'model_version': '${TEST_MODEL_VERSION_2}'

    ${resp}=        Shell  legionctl --verbose md get
                    Should Be Equal As Integers     ${resp.rc}              0
                    Should contain              ${resp.stdout}      ${TEST_MD_NAME_1}
                    Should contain              ${resp.stdout}      ${TEST_MD_NAME_2}

Check default model urls
    [Setup]  NONE
    [Tags]  apps
    Get token from EDI   ${TEST_MD_NAME_1}  ${TEST_MD_NAME_1}

    Run EDI deploy and check model started  ${TEST_MD_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_1}  ${TEST_MD_NAME_1}

    Get token from EDI   ${TEST_MD_NAME_1}  ${TEST_MD_NAME_1}
    StrictShell  legionctl --verbose model info --md ${TEST_MD_NAME_1} --jwt ${token}

    Run EDI deploy and check model started  ${TEST_MD_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION_2}  ${TEST_MD_NAME_2}

    Get token from EDI   ${TEST_MD_NAME_2}  ${TEST_MD_NAME_2}
    ${res}=  StrictShell  legionctl --verbose model info --md ${TEST_MD_NAME_2} --jwt ${token}

    Shell  legionctl --verbose model info --md ${TEST_MD_NAME_1} --jwt ${token}

Invoke two models
    [Documentation]  Check that config holds model jwts separately
    [Tags]  apps
    ${res}=  Shell  legionctl generate-token --md ${TEST_MD_NAME_1} --role ${TEST_MD_NAME_1}
             Should be equal  ${res.rc}  ${0}
    ${MD_TOKEN_1}=  Set variable  ${res.stdout}

    ${res}=  Shell  legionctl generate-token --md ${TEST_MD_NAME_2} --role ${TEST_MD_NAME_2}
             Should be equal  ${res.rc}  ${0}
    ${MD_TOKEN_2}=  Set variable  ${res.stdout}

    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME_1} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --md ${TEST_MD_NAME_2} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --mr ${TEST_MD_NAME_1} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --mr ${TEST_MD_NAME_2} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${TEST_MD_NAME_1} -p a=1 -p b=2
         Should not be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${TEST_MD_NAME_2} -p a=1 -p b=2
         Should not be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${TEST_MD_NAME_1} -p a=1 -p b=2 --jwt ${MD_TOKEN_1}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${TEST_MD_NAME_2} -p a=1 -p b=2 --jwt ${MD_TOKEN_2}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url ${EDGE_URL}/model/${TEST_MD_NAME_1} -p a=1 -p b=2 --jwt ${MD_TOKEN_1}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --url ${EDGE_URL}/model/${TEST_MD_NAME_2} -p a=1 -p b=2 --jwt ${MD_TOKEN_2}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
