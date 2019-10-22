*** Variables ***
${RES_DIR}              ${CURDIR}/resources
${LOCAL_CONFIG}        legion/config_deployment_dep_undep
${MD_SIMPLE_MODEL}     simple-model-dep-undep

*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        10 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             legion.robot.libraries.k8s.K8s  ${LEGION_DEPLOYMENT_NAMESPACE}
Library             legion.robot.libraries.utils.Utils
Library             Collections
Suite Setup         Run Keywords  Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                               Login to the edi and edge  AND
...                               Cleanup resources
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}

Force Tags        deployment  edi  cli

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose dep delete --id ${MD_SIMPLE_MODEL} --ignore-not-found

File not found
    [Arguments]  ${command}
        ${res}=  Shell  legionctl --verbose dep ${command} -f wrong-file
                 Should not be equal  ${res.rc}  ${0}
                 Should contain       ${res.stderr}  Resource file 'wrong-file' not found

*** Test Cases ***
Check EDI deploy procedure
    [Documentation]  Try to deploy dummy model through EDI console
    [Teardown]  Cleanup resources
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/simple-model.deployment.legion.yaml

    Check model started  ${MD_SIMPLE_MODEL}

Update model deployment
    [Documentation]  Check model deployment upgrade
    [Teardown]  Cleanup resources
    [Tags]  kek
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/simple-model.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL}

    ${res}=  StrictShell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json '{"columns": ["a","b"],"data": [[1.0,2.0]]}'
    ${actual_response}=    Evaluate     json.loads("""${res.stdout}""")    json
    ${expected_response}=   evaluate  {'prediction': [[42]], 'columns': ['result']}
    Dictionaries Should Be Equal    ${actual_response}    ${expected_response}

    Run EDI apply from model packaging  ${MP_COUNTER_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/updated-simple-model.deployment.legion.yaml
    Check model started  ${MD_SIMPLE_MODEL}

    # Check new REST API
    ${res}=  StrictShell  legionctl --verbose model invoke --md ${MD_SIMPLE_MODEL} --json '{"columns": ["a","b"],"data": [[1.0,2.0]]}'
    ${actual_response}=    Evaluate     json.loads("""${res.stdout}""")    json
    ${expected_response}=   evaluate  {'prediction': [[1]], 'columns': ['result']}
    Dictionaries Should Be Equal    ${actual_response}    ${expected_response}

    # Check new resources
    ${res}=  StrictShell  legionctl dep get --id ${MD_SIMPLE_MODEL} -o jsonpath='[*].status.deployment'
    ${model_deployment}=  Get model deployment  ${res.stdout}  ${LEGION_DEPLOYMENT_NAMESPACE}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  333m  ${model_resources.limits["cpu"]}
    Should be equal  333Mi  ${model_resources.limits["memory"]}
    Should be equal  222m  ${model_resources.requests["cpu"]}
    Should be equal  222Mi  ${model_resources.requests["memory"]}

    # Check new number of replicas
    ${res}=  StrictShell  legionctl dep get --id ${MD_SIMPLE_MODEL} -o jsonpath='[*].status.replicas'
    should be equal as integers  ${2}  ${res.stdout}

Deploy with custom memory and cpu
    [Documentation]  Deploy with custom memory and cpu
    [Teardown]  Cleanup resources
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/custom-resources.deployment.legion.yaml

    ${res}=  StrictShell  legionctl dep get --id ${MD_SIMPLE_MODEL} -o jsonpath='[*].status.deployment'
    ${model_deployment}=  Get model deployment  ${res.stdout}  ${LEGION_DEPLOYMENT_NAMESPACE}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  333m  ${model_resources.limits["cpu"]}
    Should be equal  333Mi  ${model_resources.limits["memory"]}
    Should be equal  222m  ${model_resources.requests["cpu"]}
    Should be equal  222Mi  ${model_resources.requests["memory"]}

Check setting of default resource values
    [Documentation]  Deploy setting of default resource values
    [Teardown]  Cleanup resources
    Run EDI deploy from model packaging  ${MP_SIMPLE_MODEL}  ${MD_SIMPLE_MODEL}  ${RES_DIR}/simple-model.deployment.legion.yaml

    ${res}=  StrictShell  legionctl dep get --id ${MD_SIMPLE_MODEL} -o jsonpath='[*].status.deployment'
    ${model_deployment}=  Get model deployment  ${res.stdout}  ${LEGION_DEPLOYMENT_NAMESPACE}
    LOG  ${model_deployment}

    ${model_resources}=  Set variable  ${model_deployment.spec.template.spec.containers[0].resources}
    Should be equal  256m  ${model_resources.limits["cpu"]}
    Should be equal  256Mi  ${model_resources.limits["memory"]}
    Should be equal  128m  ${model_resources.requests["cpu"]}
    Should be equal  128Mi  ${model_resources.requests["memory"]}

File with entitiy not found
    [Documentation]  Invoke Model Deployment commands with not existed file
    [Template]  File not found
    command=create
    command=edit
