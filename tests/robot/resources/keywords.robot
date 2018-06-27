*** Settings ***
Documentation       Legion robot resources
Resource            variables.robot
Library             String
Library             OperatingSystem
Library             Collections
Library             legion_test.robot.K8s
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Utils
Library             legion_test.robot.Grafana
Library             legion_test.robot.Airflow

*** Keywords ***
Connect to enclave Grafana
    [Arguments]           ${enclave}
    Connect to Grafana    ${HOST_PROTOCOL}://grafana-${enclave}.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}

Connect to Jenkins endpoint
    Connect to Jenkins    ${HOST_PROTOCOL}://jenkins.${HOST_BASE_DOMAIN}                                 ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}

Connect to enclave Airflow
    [Arguments]           ${enclave}
    Connect to Airflow    ${HOST_PROTOCOL}://airflow-${enclave}.${HOST_BASE_DOMAIN}

Connect to enclave Flower
    [Arguments]           ${enclave}
    Connect to Flower    ${HOST_PROTOCOL}://flower-${enclave}.${HOST_BASE_DOMAIN}

Run EDI inspect
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for enclave ${enclave} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI inspect with parse
    [Documentation]  get parsed inspect result for validation and logs it
    [Arguments]           ${enclave}
    ${edi_state} =        Run EDI inspect                                ${enclave}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.output}
    Log                   ${parsed}
    [Return]              ${parsed}

Run EDI deploy
    [Documentation]  run legionctl 'deploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${image}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl deploy ${image} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for image ${image} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI undeploy by model version and check
    [Arguments]           ${enclave}    ${model_id}    ${model_ver}
    ${edi_state}=                Run EDI undeploy with version  ${enclave}   ${model_id}    ${model_ver}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should Be Empty              ${edi_state.output}
    ${edi_state} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.output}    ${model_ver}

Run EDI undeploy model without version and check
    [Arguments]           ${enclave}    ${model_id}
    ${edi_state}=                Run EDI undeploy without version  ${enclave}   ${model_id}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should Be Empty              ${edi_state.output}
    ${edi_state} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.output}    ${model_id}

Run EDI undeploy by model version and check error
    [Arguments]           ${enclave}    ${model_id}    ${model_ver}    ${error_expected}
    ${edi_state}=                Run EDI undeploy with version  ${enclave}   ${model_id}    ${model_ver}
    Should Be Equal As Integers  ${edi_state.rc}        1
    Should contains              ${edi_state.output}    ${error_expected}

Run EDI undeploy model without version and check error
    [Arguments]           ${enclave}    ${model_id}    ${error_expected}
    ${edi_state}=                Run EDI undeploy without version  ${enclave}   ${model_id}
    Should Be Equal As Integers  ${edi_state.rc}        1
    Should contains              ${edi_state.output}    ${error_expected}

Run EDI scale model with version and check
    [Arguments]           ${enclave}    ${image}    ${model_id}   ${scale_count}   ${model_ver}
    ${scale_result} =            Run EDI scale with version   ${enclave}   ${model_id}    ${scale_count}     ${model_ver}
    Should Be Equal As Integers  ${scale_result.rc}   0
    Should Be Empty              ${scale_result.output}
    Sleep            10  # because no way to control explicitly scaling the model inside
    # TODO remove sleep
    ${parsed_edi_state} =        Run EDI inspect with parse     ${enclave}
    ${target_model} =            Find model information in edi  ${parsed_edi_state}  ${model_id}
    Log  ${target_model}
    Verify model info from edi    ${target_model}   ${model_id}    ${image}   ${model_ver}  ${scale_count}

Run EDI scale model and check error
    [Arguments]           ${enclave}    ${model_id}   ${scale_count}   ${model_ver}    ${error_expected}
    ${scale_result} =            Run EDI scale with version   ${enclave}   ${model_id}    ${scale_count}     ${model_ver}
    Should Be Equal As Integers  ${scale_result.rc}   1
    Should contain               ${scale_result.output}  ${error_expected}

Run EDI scale model without version and check error
    [Arguments]           ${enclave}    ${model_id}   ${scale_count}   ${error_expected}
    ${scale_result} =            Run EDI scale  ${enclave}   ${model_id}    ${scale_count}
    Should Be Equal As Integers  ${scale_result.rc}   1
    Should contain               ${scale_result.output}  ${error_expected}

Run EDI scale model without version and check
    [Arguments]           ${enclave}    ${image}    ${model_id}   ${scale_count}
    ${scale_result} =            Run EDI scale  ${enclave}   ${model_id}    ${scale_count}
    Should Be Equal As Integers  ${scale_result.rc}   0
    Should Be Empty              ${scale_result.output}
    Sleep            10  # because no way to control explicitly scaling the model inside
    # TODO remove sleep
    ${parsed_edi_state} =        Run EDI inspect with parse     ${enclave}
    ${target_model} =            Find model information in edi  ${parsed_edi_state}  ${model_id}
    Log  ${target_model}
    Verify model info from edi    ${target_model}   ${model_id}    ${image}   ${scale_count}

Run EDI deploy and check model started
    [Arguments]           ${enclave}    ${image}      ${model_id}   ${model_ver}
    ${edi_state}=   Run EDI deploy      ${enclave}    ${image}
    Should Be Equal As Integers  ${edi_state.rc}   0
    Should Be Empty              ${edi_state.output}
    ${response}=    Check model started ${enclave}    ${model_id}
    Should contain               ${response}       version=${model_ver}

Run EDI inspect and verify info from edi
    [Arguments]           ${enclave}    ${image}    ${model_id}    ${model_ver}
    ${edi_state} =      Run EDI inspect with parse     ${enclave}
    ${target_model} =   Find model information in edi  ${edi_state}     ${model_id}    ${model_ver}
    Log  ${target_model}
    Verify model info from edi    ${target_model}   ${model_id}    ${image}   ${model_ver} 1

Check model started
    [Documentation]  check if model run in container by http request
    [Arguments]           ${enclave}  ${model_id}
    ${resp}=              Check_model_started   ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN}/api/model/${model_id}/info
    Log                   ${resp}
    [Return]              ${resp}

Run EDI undeploy with version
    [Arguments]           ${enclave}    ${model_id}  ${model_version}
    ${edi_state} =  Run And Return Rc And Output   legionctl undeploy ${model_id} --model-version ${model_version} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Run EDI undeploy without version
    [Documentation]  run legionctl 'undeploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl undeploy ${model_id} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for model_id ${model_id} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI scale
    [Documentation]  run legionctl 'scale command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}     ${new_scale}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl scale ${model_id} ${new_scale} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for model_id ${model_id} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI scale with version
    [Documentation]  run legionctl 'scale command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}     ${new_scale}    ${model_ver}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl scale ${model_id} ${new_scale} --model-version ${model_ver} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for model_id ${model_id} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Verify model info from edi
    [Arguments]      ${target_model}       ${model_id}      ${model_image}      ${model_version}    ${scale_num}
    Should Be Equal  ${target_model[0]}    ${model_id}      invalid model id
    Should Be Equal  ${target_model[1]}    ${model_image}   invalid model image
    Should Be Equal  ${target_model[2]}    ${model_version} invalid model version
    Should Be Equal  ${target_model[3]}    ${scale_num}     invalid actual scales
    Should Be Equal  ${target_model[4]}    ${scale_num}     invalid desired scale
    Should Be Empty  ${target_model[5]}                     got some errors ${target_model[5]}

Test model pipeline
    [Arguments]          ${model_name}                      ${enclave}=${CLUSTER_NAMESPACE}
    Run Jenkins job                                         DYNAMIC MODEL ${model_name}   Enclave=${enclave}
    Wait Jenkins job                                        DYNAMIC MODEL ${model_name}   600
    Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    Log                  Model meta is ${model_meta}
    ${model_path} =      Get From Dictionary                ${model_meta}                 modelPath
    ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    ${model_version} =   Get From Dictionary                ${model_meta}                 modelVersion
    ${model_path} =	     Get Regexp Matches	                ${model_path}                 (.*)://[^/]+/(?P<path>.*)   path
    ${model_url} =       Set Variable                       ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}/${model_path[0]}
    Log                  External model URL is ${model_url}
    Check remote file exists                                ${model_url}                  ${SERVICE_ACCOUNT}          jonny
    Connect to enclave Grafana                              ${enclave}
    Dashboard should exists                                 ${model_id}
    Sleep                15s
    Metric should be presented                              ${model_id}                   ${model_version}
    ${edi_state}=        Run      legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                  State of ${model_id} is ${edi_state}

Check if all enclave domains are registered
    [Arguments]             ${enclave}
    :FOR    ${enclave_subdomain}    IN    @{ENCLAVE_SUBDOMAINS}
    \   Check domain exists  ${enclave_subdomain}-${enclave}.${HOST_BASE_DOMAIN}

Run, wait and check jenkins jobs for enclave
    [Arguments]             ${enclave}
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
    \    Test model pipeline  ${model_name}  ${enclave}