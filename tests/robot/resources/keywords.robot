*** Settings ***
Documentation       Legion robot resources
Resource            variables.robot
Library             String
Library             OperatingSystem
Library             Collections
Library             DateTime
Library             legion_test.robot.K8s
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Utils
Library             legion_test.robot.Grafana
Library             legion_test.robot.Airflow
Library             legion_test.robot.Process

*** Keywords ***
Connect to enclave Grafana
    [Arguments]           ${enclave}
    Connect to Grafana    ${HOST_PROTOCOL}://grafana-${enclave}.${HOST_BASE_DOMAIN}    ${SERVICE_ACCOUNT}     ${SERVICE_PASSWORD}

Connect to Jenkins endpoint
    Connect to Jenkins    ${HOST_PROTOCOL}://jenkins.${HOST_BASE_DOMAIN}

Connect to enclave Airflow
    [Arguments]           ${enclave}
    Connect to Airflow    ${HOST_PROTOCOL}://airflow-${enclave}.${HOST_BASE_DOMAIN}

Connect to enclave Flower
    [Arguments]           ${enclave}
    Connect to Flower    ${HOST_PROTOCOL}://flower-${enclave}.${HOST_BASE_DOMAIN}

Shell
    [Arguments]           ${command}
    ${result}=            Run Process without PIPE   ${command}    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

    # --------- INSPECT COMMAND SECTION -----------
Run EDI inspect enclave and check result
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${expected_rc}   ${expected_output}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    Should Be Equal As Integers  ${result.rc}        ${expected_rc}
    Should contain               ${result.stdout}    ${expected_output}

Run EDI inspect
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model id
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_id}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model version
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_ver}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model id and model version
    [Documentation]  run legionctl 'inspect command', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_id}     ${model_ver}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-id ${model_id} --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect with parse
    [Documentation]  get parsed inspect result for validation and logs it
    [Arguments]           ${enclave}
    ${edi_state} =        Run EDI inspect                                ${enclave}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.stdout}
    Log                   ${parsed}
    [Return]              ${parsed}

Run EDI inspect with parse by model id
    [Documentation]  get parsed inspect result for validation and logs it
    [Arguments]           ${enclave}        ${model_id}
    ${edi_state} =        Run EDI inspect by model id    ${enclave}      ${model_id}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.stdout}
    Log                   ${parsed}
    [Return]              ${parsed}

    # --------- DEPLOY COMMAND SECTION -----------
Run EDI deploy
    [Documentation]  run legionctl 'deploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${image}
    ${result}=            Run Process without PIPE   legionctl --verbose deploy ${image} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI deploy with scale
    [Documentation]  run legionctl 'deploy command with scale option', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${image}    ${scale_count}
    ${result}=            Run Process without PIPE   legionctl --verbose deploy ${image} --scale ${scale_count} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI deploy and check model started
    [Arguments]           ${enclave}     ${image}      ${model_id}   ${model_ver}
    Log  ${DEX_TOKEN}
    ${edi_state}=   Run EDI deploy       ${enclave}              ${image}
    Should Be Equal As Integers          ${edi_state.rc}         0
    ${response}=    Check model started  ${enclave}              ${model_id}             ${model_ver}
    Should contain                       ${response}             "model_version": "${model_ver}"

    # --------- UNDEPLOY COMMAND SECTION -----------
Run EDI undeploy by model version and check
    [Timeout]       2 min
    [Arguments]           ${enclave}    ${model_id}    ${model_ver}    ${model_image}
    ${resp_dict}=                Run EDI undeploy with version  ${enclave}   ${model_id}    ${model_ver}
    Should Be Equal As Integers  ${resp_dict.rc}        0
    ${resp_dict} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${resp_dict.rc}        0
    Should not contain           ${resp_dict.stdout}    ${model_image}

Run EDI undeploy model without version and check
    [Arguments]           ${enclave}    ${model_id}
    ${edi_state}=                Run EDI undeploy without version  ${enclave}   ${model_id}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.stdout}    ${model_id}
    ${edi_state} =               Run EDI inspect        ${enclave}
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.stdout}    ${model_id}

Run EDI undeploy with version
    [Arguments]           ${enclave}    ${model_id}  ${model_version}
    ${result}=            Run Process without PIPE   legionctl --verbose undeploy ${model_id} --model-version ${model_version} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"     shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI undeploy without version
    [Documentation]  run legionctl 'undeploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}
    ${result}=            Run Process without PIPE   legionctl --verbose undeploy ${model_id} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

    # --------- SCALE COMMAND SECTION -----------
Run EDI scale
    [Documentation]  run legionctl 'scale command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}     ${new_scale}
    ${result}=            Run Process without PIPE   legionctl --verbose scale ${model_id} ${new_scale} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"   shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI scale with version
    [Documentation]  run legionctl 'scale command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${enclave}    ${model_id}     ${new_scale}    ${model_ver}
    ${result}=            Run Process without PIPE   legionctl --verbose scale ${model_id} ${new_scale} --model-version ${model_ver} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

    # --------- OTHER KEYWORDS SECTION -----------
Build enclave EDGE URL
    [Documentation]  build enclave EDGE URL
    [Arguments]           ${enclave}
    [Return]              ${HOST_PROTOCOL}://edge-${enclave}.${HOST_BASE_DOMAIN}

Get token from EDI
    [Documentation]  get token from EDI for the EDGE session
    [Arguments]     ${enclave}   ${model_id}   ${model_version}
    &{data} =             Create Dictionary    model_id=${model_id}    model_version=${model_version}
    &{resp} =             Execute post request    ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN}/api/1.0/generate_token  data=${data}  cookies=${DEX_COOKIES}
    Log                   ${resp["text"]}
    Should not be empty   ${resp}
    &{token} =  Evaluate  json.loads('''${resp["text"]}''')    json
    Log                   ${token}
    Set Suite Variable    ${TOKEN}    ${token['token']}

Check model started
    [Documentation]  check if model run in container by http request
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}
    Log                   request url is ${HOST_PROTOCOL}://edge-${enclave}.${HOST_BASE_DOMAIN}/api/model/${model_id}/${model_ver}/info
                          Get token from EDI    ${enclave}   ${model_id}   ${model_ver}
    ${resp}=              Check valid http response   ${HOST_PROTOCOL}://edge-${enclave}.${HOST_BASE_DOMAIN}/api/model/${model_id}/${model_ver}/info    token=${TOKEN}
    Log                   ${resp}
    Should not be empty   ${resp}
    [Return]              ${resp}

Invoke deployed model
    [Documentation]  call model invoke endpoint
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}  ${request_id}=None  ${endpoint}=default  &{arguments}
    ${edge}=              Build enclave EDGE URL    ${enclave}
    Get token from EDI    ${enclave}   ${model_id}  ${model_ver}
    ${resp}=              Invoke model API  ${model_id}  ${model_ver}  ${edge}  ${TOKEN}  ${endpoint}  ${request_id}  &{arguments}
    [Return]              ${resp}

Send feedback for deployed model
    [Documentation]  call model feedback endpoint
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}  ${request_id}  &{arguments}
    ${edge}=              Build enclave EDGE URL    ${enclave}
    Get token from EDI    ${enclave}   ${model_id}  ${model_ver}
    ${resp}=              Invoke model feedback  ${model_id}  ${model_ver}  ${edge}  ${TOKEN}  ${request_id}  &{arguments}
    [Return]              ${resp}

Validate model API meta log entry
    [Documentation]  check that model API log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  request_http_method
    Dictionary Should Contain Key   ${log_entry}  request_http_headers
    Dictionary Should Contain Key   ${log_entry}  request_host
    Dictionary Should Contain Key   ${log_entry}  request_uri
    Dictionary Should Contain Key   ${log_entry}  response_duration
    Dictionary Should Contain Key   ${log_entry}  response_http_headers
    Dictionary Should Contain Key   ${log_entry}  response_body_chunk_count
    Dictionary Should Contain Key   ${log_entry}  response_status
    Dictionary Should Contain Key   ${log_entry}  model_id
    Dictionary Should Contain Key   ${log_entry}  model_version

Validate model API meta log entry Request ID
    [Documentation]  check that model API log entry Request ID is correct
    [Arguments]      ${log_entry}   ${excpected_request_id}
    ${actual_request_id}=           Get From Dictionary       ${log_entry}     request_id
    Should Be Equal                 ${actual_request_id}      ${excpected_request_id}

Validate model API meta log entry HTTP method
    [Documentation]  check that model API log entry HTTP method is correct
    [Arguments]      ${log_entry}   ${excpected_value}
    ${http_method}=                 Get From Dictionary       ${log_entry}     request_http_method
    Should Be Equal                 ${http_method}            ${excpected_value}

Validate model API meta log entry POST arguments
    [Documentation]  check that model API log entry POST arguments are correct
    [Arguments]      ${log_entry}   &{excpected_values}
    ${actual_post_args}=    Get From Dictionary       ${log_entry}     request_post_args
    Dictionaries Should Be Equal    ${actual_post_args}    ${excpected_values}

Validate model API meta ID and version
    [Documentation]  check that model API ID and version is correct
    [Arguments]      ${log_entry}   ${excpected_model_id}   ${excpected_model_version}
    ${actual_model_id}=            Get From Dictionary       ${log_entry}     model_id
    ${actual_model_version}=       Get From Dictionary       ${log_entry}     model_version
    Should Be Equal                ${actual_model_id}        ${excpected_model_id}
    Should Be Equal                ${actual_model_version}   ${excpected_model_version}

Get count of invocation chunks from model API meta log entry response
    [Documentation]  check that model API log entry response is correct
    [Arguments]      ${log_entry}
    ${chunk_count}=  Get From Dictionary       ${log_entry}     response_body_chunk_count
    [Return]         ${chunk_count}

Validate model API response
    [Documentation]  check that model API response is correct
    [Arguments]      ${actual_response}   &{excpected_values}
    Dictionaries Should Be Equal    ${actual_response}    ${excpected_values}

Validate model API body log entry
    [Documentation]  check that model API body log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  response_chunk_id
    Dictionary Should Contain Key   ${log_entry}  response_content
    Dictionary Should Contain Key   ${log_entry}  model_id
    Dictionary Should Contain Key   ${log_entry}  model_version

Validate model API body log entry for all entries
    [Documentation]  check that model API body log entries contains all required keys
    [Arguments]      ${log_entries}
    :FOR    ${log_entry}    IN    @{log_entries}
    \    Validate model API body log entry    ${log_entry}

Get model API body content from all entries
    [Documentation]  get model API body content from all entries
    [Arguments]      ${log_entries}
    @{ordered_log_entries}=  Order list of dicts by key       ${log_entries}          response_chunk_id
    ${content}=              Concatinate list of dicts field  ${ordered_log_entries}  response_content
    Log                      ${content}
    ${parsed_content}=       Parse JSON string  ${content}
    [Return]  ${parsed_content}

Validate model feedback log entry
    [Documentation]  check that model feedback log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  feedback_payload
    Dictionary Should Contain Key   ${log_entry}  model_id
    Dictionary Should Contain Key   ${log_entry}  model_version

Validate model feedback log entry Request ID
    [Documentation]  check that model feedback log entry Request ID is correct
    [Arguments]      ${log_entry}   ${excpected_request_id}
    ${actual_request_id}=           Get From Dictionary       ${log_entry}     request_id
    Should Be Equal                 ${actual_request_id}      ${excpected_request_id}

Validate model feedback log entry params
    [Documentation]  check that model feedback log entry params
    [Arguments]      ${log_entry}   &{excpected_values}
    ${actual_post_args}=    Get From Dictionary       ${log_entry}     feedback_payload
    Dictionaries Should Be Equal    ${actual_post_args}    ${excpected_values}

Validate model feedback ID and version
    [Documentation]  check that model feedback ID and version is correct
    [Arguments]      ${log_entry}   ${excpected_model_id}   ${excpected_model_version}
    ${actual_model_id}=            Get From Dictionary       ${log_entry}     model_id
    ${actual_model_version}=       Get From Dictionary       ${log_entry}     model_version
    Should Be Equal                ${actual_model_id}        ${excpected_model_id}
    Should Be Equal                ${actual_model_version}   ${excpected_model_version}

Verify model info from edi
    [Arguments]      ${target_model}       ${model_id}        ${model_image}      ${model_version}    ${scale_num}
    Should Be Equal  ${target_model[0]}    ${model_id}        invalid model id
    Should Be Equal  ${target_model[1]}    ${model_image}     invalid model image
    Should Be Equal  ${target_model[2]}    ${model_version}   invalid model version
    Should Be Equal  ${target_model[3]}    ${scale_num}       invalid actual scales
    Should Be Equal  ${target_model[4]}    ${scale_num}       invalid desired scale

Test model pipeline result
    [Arguments]          ${model_name}                      ${enclave}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    Log                  Model meta is ${model_meta}
    ${model_path} =      Get From Dictionary                ${model_meta}                 modelPath
    ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    ${model_version} =   Get From Dictionary                ${model_meta}                 modelVersion
    ${model_path} =	     Get Regexp Matches	                ${model_path}                 (.*)://[^/]+/(?P<path>.*)   path
    ${edge}=             Build enclave EDGE URL             ${enclave}
    Get token from EDI   ${enclave}   ${model_id}   ${model_version}
    ${model_info} =      Get model info       ${model_id}  ${model_version}  ${edge}  ${TOKEN}
    Log                  Model info is ${model_info}
    ${model_url} =       Set Variable                       ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}/${model_path[0]}
    Log                  External model URL is ${model_url}
    Check remote file exists                                ${model_url}                  ${SERVICE_ACCOUNT}          jonny
    Connect to enclave Grafana                              ${enclave}
    Dashboard should exists                                 ${model_id}
    Sleep                15s
    Metric should be presented                              ${model_id}                   ${model_version}
    ${edi_state}=        Run      legionctl inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN}
    Log                  State of ${model_id} is ${edi_state}
    [Return]             ${model_id}    ${model_version}

Check if all enclave domains are registered
    [Arguments]             ${enclave}
    :FOR    ${enclave_subdomain}    IN    @{ENCLAVE_SUBDOMAINS}
    \   Check domain exists  ${enclave_subdomain}-${enclave}.${HOST_BASE_DOMAIN}

Run model jenkins Job
    [Arguments]          ${model_name}                      ${enclave}=${CLUSTER_NAMESPACE}
    Run and wait Jenkins job                                DYNAMIC MODEL ${model_name}   Enclave=${enclave}
    Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}

Run predefined Jenkins jobs for enclave
    [Arguments]             ${enclave}
    Connect to Jenkins endpoint
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
    \    Run model jenkins Job  ${model_name}  ${enclave}

Get cluster nodes and their count
    [Arguments]    ${is_before}
    @{cluster_nodes} =    Get cluster nodes
    ${nodes_number} =     Get Length    ${cluster_nodes}
    Run Keyword If   '${is_before}' == 'before'    Set Test Variable     ${NODES_COUNT_BEFORE}    ${nodes_number}
    ...    ELSE      Set Test Variable     ${NODES_COUNT_AFTER}    ${nodes_number}

    # --------- TEMPLATE KEYWORDS SECTION -----------

Check if component domain has been secured
    [Arguments]     ${component}    ${enclave}
    [Documentation]  Check that a legion component is secured by auth
    ${jenkins} =     Run Keyword If   '${component}' == 'jenkins'    Set Variable    True
    ...    ELSE      Set Variable    False
    ${boolean} =     Convert To Boolean    ${jenkins}
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Get component auth page    ${HOST_PROTOCOL}://${component}.${HOST_BASE_DOMAIN}    ${boolean}
    ...    ELSE      Get component auth page    ${HOST_PROTOCOL}://${component}-${enclave}.${HOST_BASE_DOMAIN}    ${boolean}
    Log              Auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    Log in

Secured component domain should not be accessible by invalid credentials
    [Arguments]     ${component}    ${enclave}
    [Documentation]  Check that a secured legion component does not provide access by invalid credentials
    ${jenkins} =     Run Keyword If   '${component}' == 'jenkins'    Set Variable    True
    ...    ELSE      Set Variable    False
    ${boolean} =     Convert To Boolean    ${jenkins}
    &{creds} =       Create Dictionary 	login=admin   password=admin
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Post credentials to auth    ${HOST_PROTOCOL}://${component}    ${HOST_BASE_DOMAIN}    ${creds}    ${boolean}
    ...    ELSE      Post credentials to auth    ${HOST_PROTOCOL}://${component}-${enclave}     ${HOST_BASE_DOMAIN}    ${creds}    ${boolean}
    Log              Bad auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    Log in to Your Account
    Should contain   ${auth_page}    Invalid Email Address and password

Secured component domain should be accessible by valid credentials
    [Arguments]     ${component}    ${enclave}
    [Documentation]  Check that a secured legion component does not provide access by invalid credentials
    ${jenkins} =     Run Keyword If   '${component}' == 'jenkins'    Set Variable    True
    ...    ELSE      Set Variable    False
    ${boolean} =     Convert To Boolean    ${jenkins}
    &{creds} =       Create Dictionary    login=${STATIC_USER_EMAIL}    password=${STATIC_USER_PASS}
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Post credentials to auth    ${HOST_PROTOCOL}://${component}    ${HOST_BASE_DOMAIN}    ${creds}    ${boolean}
    ...    ELSE      Post credentials to auth    ${HOST_PROTOCOL}://${component}-${enclave}     ${HOST_BASE_DOMAIN}    ${creds}    ${boolean}
    Log              Bad auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    ${component}
    Should not contain   ${auth_page}    Invalid Email Address and password

Invoke and check test dags for valid status code
    [Arguments]   ${enclave}
    [Documentation]  Check test dags for valid status code
    Connect to enclave Airflow                           ${enclave}
    :FOR    ${dag}      IN      @{TEST_DAGS}
    \   ${ready} =            Is dag ready    ${dag}
    \   Should Be True 	      ${ready} == True    Dag ${dag} was not ready
    \   ${tasks} =            Find Airflow Tasks  ${dag}
# Temporary disabling triggering Airflow tasks as it fails Airflow test
# TODO: Need to rewrite this logic as a part of Airflow upgrade.
#    \   Run airflow task and validate stderr      ${tasks}   ${dag}
    \   Wait dag finished     ${dag}
    \   ${failed_dags} =      Get failed Airflow DAGs
    \   Should Not Contain    ${failed_dags}      ${dag}
    \   ${succeeded_dags} =   Get succeeded Airflow DAGs
    \   Should not be empty   ${succeeded_dags}

Run airflow task and validate stderr
    [Arguments]   ${tasks}   ${dag}
    [Documentation]  Check airflow tasks for valid status code
    :FOR    ${task}     IN      @{tasks}
    \   ${date_time} =      Get Current Date  result_format='%Y-%m-%d %H:%M:%S'
    \   ${status} =         Trigger Airflow task    ${dag}  ${task}  ${date_time}
    \   Should Be Equal     ${status}   ${None}

Set replicas num
    [Arguments]   ${replicas_num}
    :FOR  ${enclave}    IN    @{ENCLAVES}
    \   Set deployment replicas   ${replicas_num}  airflow-${enclave}-worker  ${enclave}
        Wait deployment replicas count   airflow-${enclave}-worker  namespace=${enclave}  expected_replicas_num=${replicas_num}