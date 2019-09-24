*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}        legion/config_deployment_multi_version
${MD_SIMPLE_MODEL_1}   simple-model-multiver-1
${MD_SIMPLE_MODEL_2}   simple-model-multiver-2

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}
Test Teardown       Cleanup resources
Force Tags          deployment  edi  cli

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose dep delete --id ${MD_SIMPLE_MODEL_1} --ignore-not-found
    StrictShell  legionctl --verbose dep delete --id ${MD_SIMPLE_MODEL_2} --ignore-not-found

*** Test Cases ***
Check EDI deploy 2 models with different versions but the same name
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_1}  ${RES_DIR}/simple-model-1.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL_1}

    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_2}  ${RES_DIR}/simple-model-2.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL_2}

Check EDI deploy 2 models with the same image
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_1}  ${RES_DIR}/simple-model-1.deployment.legion.yaml
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_2}  ${RES_DIR}/simple-model-2.deployment.legion.yaml

    ${resp}=        StrictShell  legionctl --verbose dep get
                    Should contain              ${resp.stdout}      ${MD_SIMPLE_MODEL_1}
                    Should contain              ${resp.stdout}      ${MD_SIMPLE_MODEL_2}

Check default model urls
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_1}  ${RES_DIR}/simple-model-1.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL_1}

    StrictShell  legionctl --verbose model info --md ${MD_SIMPLE_MODEL_1} --jwt ${AUTH_TOKEN}

    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_2}  ${RES_DIR}/simple-model-2.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL_2}

    ${res}=  StrictShell  legionctl --verbose model info --md ${MD_SIMPLE_MODEL_2} --jwt ${AUTH_TOKEN}

    Shell  legionctl --verbose model info --md ${MD_SIMPLE_MODEL_1} --jwt ${AUTH_TOKEN}

Invoke two models
    [Documentation]  Check that config holds model jwts separately
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_1}  ${RES_DIR}/simple-model-1.deployment.legion.yaml
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL_2}  ${RES_DIR}/simple-model-2.deployment.legion.yaml

    Check model started  ${MD_SIMPLE_MODEL_1}
    Check model started  ${MD_SIMPLE_MODEL_2}

    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL_1} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL_2} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --mr ${MD_SIMPLE_MODEL_1} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --mr ${MD_SIMPLE_MODEL_2} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${MD_SIMPLE_MODEL_1} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${MD_SIMPLE_MODEL_2} --json-file ${RES_DIR}/simple-model.request.json
         Should be equal  ${res.rc}  ${0}

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${MD_SIMPLE_MODEL_1} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url-prefix /model/${MD_SIMPLE_MODEL_2} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42

    ${res}=  Shell  legionctl --verbose model invoke --url ${EDGE_URL}/model/${MD_SIMPLE_MODEL_1} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
    ${res}=  Shell  legionctl --verbose model invoke --url ${EDGE_URL}/model/${MD_SIMPLE_MODEL_2} --json-file ${RES_DIR}/simple-model.request.json --jwt ${AUTH_TOKEN}
         Should be equal  ${res.rc}  ${0}
         Should contain   ${res.stdout}  42
