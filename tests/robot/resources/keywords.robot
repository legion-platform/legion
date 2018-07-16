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

    # --------- INSPECT COMMAND SECTION -----------
Run EDI inspect enclave and check result
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${expected_rc}   ${expected_output}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for enclave ${enclave} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    Should Be Equal As Integers  ${dict.rc}        ${expected_rc}
    Should contain               ${dict.output}    ${expected_output}

Run EDI inspect
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for enclave ${enclave} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI inspect by model id
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_id}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for enclave ${enclave} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI inspect by model version
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_ver}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for enclave ${enclave} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI inspect by model id and model version
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_id}     ${model_ver}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl inspect --model-id ${model_id} --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
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

Run EDI inspect with parse by model id
    [Documentation]  get parsed inspect result for validation and logs it
    [Arguments]           ${enclave}        ${model_id}
    ${edi_state} =        Run EDI inspect by model id    ${enclave}      ${model_id}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.output}
    Log                   ${parsed}
    [Return]              ${parsed}

    # --------- DEPLOY COMMAND SECTION -----------
Run EDI deploy
    [Documentation]  run legionctl 'deploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${image}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl deploy ${image} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for image ${image} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI deploy with scale
    [Documentation]  run legionctl 'deploy command with scale option', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${image}    ${scale_count}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl deploy ${image} --scale ${scale_count} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for image ${image} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI deploy and check model started
    [Arguments]           ${enclave}     ${image}      ${model_id}   ${model_ver}
    ${edi_state}=   Run EDI deploy       ${enclave}              ${image}
    Should Be Equal As Integers          ${edi_state.rc}         0
    ${response}=    Check model started  ${enclave}              ${model_id}             ${model_ver}
    Should contain                       ${response}             "version": ${model_ver}

    # --------- UNDEPLOY COMMAND SECTION -----------
Run EDI undeploy by model version and check
    [Arguments]           ${enclave}    ${model_id}    ${model_ver}
    ${resp_dict}=                Run EDI undeploy with version  ${enclave}   ${model_id}    ${model_ver}
    Should Be Equal As Integers  ${resp_dict.rc}        0
    ${resp_dict} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${resp_dict.rc}        0
    Should not contain           ${resp_dict.output}    ${model_ver}

Run EDI undeploy model without version and check
    [Arguments]           ${enclave}    ${model_id}
    ${edi_state}=                Run EDI undeploy without version  ${enclave}   ${model_id}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.output}    ${model_id}
    ${edi_state} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.output}    ${model_id}

Run EDI undeploy with version
    [Arguments]           ${enclave}    ${model_id}  ${model_version}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl undeploy ${model_id} --model-version ${model_version} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

Run EDI undeploy without version
    [Documentation]  run legionctl 'undeploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}
    ${rc}   ${output}=    Run And Return Rc And Output   legionctl undeploy ${model_id} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI answer for model_id ${model_id} is ${output}
    ${dict}=              Create Dictionary   rc=${rc}    output=${output}
    [Return]              ${dict}

    # --------- SCALE COMMAND SECTION -----------
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

    # --------- OTHER KEYWORDS SECTION -----------
Check model started
    [Documentation]  check if model run in container by http request
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}
    Log                   request url is ${HOST_PROTOCOL}://edge-${enclave}.${HOST_BASE_DOMAIN}/api/model/${model_id}/${model_ver}/info
    ${resp}=              Check valid http response   ${HOST_PROTOCOL}://edge-${enclave}.${HOST_BASE_DOMAIN}/api/model/${model_id}/${model_ver}/info
    Log                   ${resp}
    Should not be empty   ${resp}
    Log                   ${resp}
    [Return]              ${resp}

Verify model info from edi
    [Arguments]      ${target_model}       ${model_id}        ${model_image}      ${model_version}    ${scale_num}
    Should Be Equal  ${target_model[0]}    ${model_id}        invalid model id
    Should Be Equal  ${target_model[1]}    ${model_image}     invalid model image
    Should Be Equal  ${target_model[2]}    ${model_version}   invalid model version
    Should Be Equal  ${target_model[3]}    ${scale_num}       invalid actual scales
    Should Be Equal  ${target_model[4]}    ${scale_num}       invalid desired scale
    Should Be Empty  ${target_model[5]}                       got some errors ${target_model[5]}

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
    ${model_image} =     Get From Dictionary                ${model_meta}                 modelImageTagExternal
    Log                  ${model_image}
    Run Keyword If       '${model_name}' == 'Test-Summation'            Set Suite Variable    ${TEST_MODEL_IMAGE_1}       ${model_image}
    ... 	ELSE IF      '${model_name}' == 'Test-Summation-v1.1'       Set Suite Variable    ${TEST_MODEL_IMAGE_2}       ${model_image}
    Log                  TEST_MODEL_IMAGE_1 = ${TEST_MODEL_IMAGE_1}
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

Run test-summation model setup
    [Arguments]          ${model_name}                      ${enclave}
    Log                  ${model_name} and ${enclave}=${CLUSTER_NAMESPACE}
    Connect to Jenkins endpoint
    ${is_built}=    Check test-summation model is built     ${model_name}                      ${enclave}=${CLUSTER_NAMESPACE}
                    Run Keyword If                          ${is_built} == true                Log   ${model_name} is successfully built!
    ... 	        ELSE IF                                 ${is_built} == false               Build test-summation model       ${model_name}       ${enclave}=${CLUSTER_NAMESPACE}
    ... 	        ELSE                                    Log                                Could not build model!!!


Check test-summation model is built
    [Arguments]          ${model_name}                      ${enclave}
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
    Run Keyword If       ${model_name} == Test-Summation      Set Suite Variable   ${TEST_MODEL_IMAGE_1}              ${model_url}
    ... 	             ELSE IF                ${model_name} == Test-Summation-v1.1            Set Suite Variable    ${TEST_MODEL_IMAGE_1}              ${model_url}
    ${edi_state}=        Run      legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                  State of ${model_id} is ${edi_state}
    [Return]             true

Build test-summation model
    [Arguments]          ${model_name}                      ${enclave}
    Run Jenkins job                                         DYNAMIC MODEL ${model_name}   Enclave=${enclave}
    Wait Jenkins job                                        DYNAMIC MODEL ${model_name}   600
    Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html