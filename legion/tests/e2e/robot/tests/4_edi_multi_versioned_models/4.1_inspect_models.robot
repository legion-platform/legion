*** Variables ***
${LOCAL_CONFIG}  legion/config_4_1
${TEST_MODEL_ID}         41
${TEST_MODEL_VERSION_1}  11
${TEST_MODEL_VERSION_2}  22
${TEST_MODEL_NAME_1}     stub-model-41-11
${TEST_MODEL_NAME_2}     stub-model-41-22

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.grafana.Grafana
Library             legion.robot.libraries.model.Model
Library             Collections
Suite Setup         Run keywords  Choose cluster context    ${CLUSTER_NAME}  AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  \${TEST_MODEL_IMAGE_1}  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  \${TEST_MODEL_IMAGE_2}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_1}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_2}  AND
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME_1}   ${TEST_MODEL_IMAGE_1}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME_2}   ${TEST_MODEL_IMAGE_2}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}
Suite Teardown      Run keywords  Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_1}  AND
...                 Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION_2}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_1}    AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME_2}  AND
...                 Remove File  ${LOCAL_CONFIG}
Force Tags          edi  cli  enclave  multi_versions

*** Test Cases ***
Check EDI model inspect by model id return 2 models
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_NAME_1}
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_NAME_2}

Check EDI model inspect by model version return 1 model
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-version ${TEST_MODEL_VERSION_1}
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should contain                  ${resp.stdout}      ${TEST_MODEL_NAME_1}
                    Should not contain              ${resp.stdout}      ${TEST_MODEL_NAME_2}

Check EDI model inspect by model id and version return 1 model
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1}
                    Should Be Equal As Integers                 ${resp.rc}         0
                    Should contain                              ${resp.stdout}     ${TEST_MODEL_NAME_1}
                    Should not contain                          ${resp.stdout}     ${TEST_MODEL_NAME_2}

Check EDI model inspect by invalid model id
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}test
                    Should Be Equal As Integers     ${resp.rc}          0
                    Should be empty                 ${resp.stdout}

Check EDI model inspect by invalid model version
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-version ${TEST_MODEL_VERSION_1}test
                    Should Be Equal As Integers     ${resp.rc}        0
                    Should be empty                 ${resp.stdout}

Check EDI model inspect by invalid model id and invalid version
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}test --model-version ${TEST_MODEL_VERSION_1}test
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI model inspect by invalid model id and valid version
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID}test --model-version ${TEST_MODEL_VERSION_1}
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI model inspect by valid model id and invalid version
    [Tags]  apps
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1}test
                    Should Be Equal As Integers                 ${resp.rc}          0
                    Should be empty                             ${resp.stdout}

Check EDI model inspect by model id=* return all models
    [Documentation]  Try to inspect 2 models by all ids through EDI console
    ${resp}=   Shell  legionctl --verbose md get --model-id \\*
                    Should Be Equal As Integers    ${resp.rc}         0
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_NAME_1}
                    Should contain                 ${resp.stdout}     ${TEST_MODEL_NAME_2}

Check EDI model inspect by model version=* return all models
    [Documentation]  Try to inspect 2 models by all versions through EDI console
    ${resp}=   Shell  legionctl --verbose md get --model-id ${TEST_MODEL_ID} --model-version \\*
                    Should Be Equal As Integers    ${resp.rc}        0
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_NAME_1}
                    Should contain                 ${resp.stdout}    ${TEST_MODEL_NAME_2}

Invoke two models
    [Documentation]  Check that config holds model jwts separately
    [Tags]  apps
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1}
             Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl generate-token --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_2}
             Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_1} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --model-id ${TEST_MODEL_ID} --model-version ${TEST_MODEL_VERSION_2} -p a=1 -p b=2
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42