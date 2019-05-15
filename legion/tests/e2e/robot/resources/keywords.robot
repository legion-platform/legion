*** Settings ***
Documentation       Legion robot resources
Resource            variables.robot
Variables           ../load_variables_from_profiles.py
Library             String
Library             OperatingSystem
Library             Collections
Library             DateTime
Library             legion.robot.libraries.k8s.K8s  ${MODEL_TEST_ENCLAVE}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.grafana.Grafana
Library             legion.robot.libraries.process.Process

*** Keywords ***
Shell
    [Arguments]           ${command}
    ${result}=            Run Process without PIPE   ${command}    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

StrictShell
    [Arguments]           ${command}
    ${res}=   Shell  ${command}
              Should Be Equal  ${res.rc}  ${0}
    [Return]  ${res}

FailedShell
    [Arguments]           ${command}
    ${res}=   Shell  ${command}
              Should Not Be Equal  ${res.rc}  ${0}
    [Return]  ${res}

Url stay the same after dex log in
    [Arguments]  ${service_url}
    ${resp}=  Request with dex  ${service_url}  ${HOST_BASE_DOMAIN}  ${STATIC_USER_EMAIL}  ${STATIC_USER_PASS}
    should be equal  ${service_url}  ${resp.url}

Dex should raise auth error
    [Arguments]  ${service_url}
    ${resp}=  Request with dex  ${service_url}  ${HOST_BASE_DOMAIN}  admin  admin
    Log              Response for ${service_url} is ${resp}
    Should contain   ${resp.text}    Invalid Email Address and password

Connect to main Grafana
    Connect to Grafana    ${HOST_PROTOCOL}://grafana.${HOST_BASE_DOMAIN}  ${GRAFANA_USER}  ${GRAFANA_PASSWORD}

Build stub model
    [Arguments]  ${model_id}  ${model_version}  ${model_image_key_name}=\${TEST_MODEL_IMAGE}

    Delete stub model training  ${model_id}  ${model_version}
    Wait Until Keyword Succeeds  2m  5 sec  Create stub model training  ${model_id}  ${model_version}

    Wait stub model training  ${model_id}  ${model_version}

    ${model_build_status}=  Get stub model training status  ${model_id}  ${model_version}
    ${model_image}=  Get From Dictionary  ${model_build_status}  modelImage

    Set Suite Variable  ${model_image_key_name}  ${model_image}

    # --------- INSPECT COMMAND SECTION -----------
Run EDI inspect enclave and check result
    [Documentation]  run legionctl 'md get command', logs result and return dict with return code and output
    [Arguments]           ${expected_rc}   ${expected_output}
    ${result}=  Shell   legionctl --verbose md get    shell=True
    Should Be Equal As Integers  ${result.rc}        ${expected_rc}
    Should contain               ${result.stdout}    ${expected_output}

Run EDI inspect
    [Documentation]  run legionctl 'md get', logs result and return dict with return code and output
    ${result}=            Run Process without PIPE   legionctl --verbose md get --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model id
    [Documentation]  run legionctl 'md get', logs result and return dict with return code and output
    [Arguments]           ${model_id}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-id ${model_id} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model version
    [Documentation]  run legionctl 'md get', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_ver}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect by model id and model version
    [Documentation]  run legionctl 'md get', logs result and return dict with return code and output
    [Arguments]           ${enclave}    ${model_id}     ${model_ver}
    ${result}=            Run Process without PIPE   legionctl --verbose inspect --model-id ${model_id} --model-version ${model_ver} --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"    shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI inspect with parse
    [Documentation]  get parsed inspect result for validation and logs it
    ${edi_state} =        Shell  legionctl --verbose md get
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.stdout}
    Log                   ${parsed}
    [Return]              ${parsed}

Run EDI inspect with parse by model id
    [Documentation]  get parsed inspect result for validation and logs it
    [Arguments]           ${model_id}
    ${edi_state} =        Shell  legionctl --verbose md get --model-id ${model_id}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state.stdout}
    Log                   ${parsed}
    [Return]              ${parsed}

    # --------- DEPLOY COMMAND SECTION -----------
Run EDI deploy
    [Documentation]  run legionctl 'deploy command', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${name}  ${image}
    ${result}=            Run Process without PIPE   legionctl --verbose md create ${name} --image ${image}  shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI deploy with scale
    [Documentation]  run legionctl 'deploy command with scale option', logs result and return dict with return code and output(for exceptions)
    [Arguments]           ${name}    ${scale_count}
    ${result}=            Run Process without PIPE   legionctl --verbose md create ${name} --replicas ${scale_count}  shell=True
    Log                   stdout = ${result.stdout}
    Log                   stderr = ${result.stderr}
    [Return]              ${result}

Run EDI deploy and check model started
    [Arguments]           ${name}     ${image}      ${model_id}   ${model_ver}
    Log  ${DEX_TOKEN}
    ${edi_state}=   Shell  legionctl --verbose md create ${name} --image ${image}
    Should Be Equal As Integers          ${edi_state.rc}         0
    ${response}=    Check model started  ${model_id}             ${model_ver}
    Should contain                       ${response}             'model_version': '${model_ver}'

    # --------- UNDEPLOY COMMAND SECTION -----------
Run EDI undeploy by model version and check
    [Timeout]       2 min
    [Arguments]           ${model_id}    ${model_version}    ${model_image}
    ${resp_dict}=                Shell  legionctl --verbose md delete --model-id ${model_id} --model-verson ${model_version}
    Should Be Equal As Integers  ${resp_dict.rc}        0
    ${resp_dict} =               Shell  legionctl --verbose md get
    Should Be Equal As Integers  ${resp_dict.rc}        0
    Should not contain           ${resp_dict.stdout}    ${model_image}

Run EDI undeploy model without version and check
    [Arguments]           ${md_name}
    ${edi_state}=                Shell  legionctl --verbose md delete ${md_name} --ignore-not-found
    Should Be Equal As Integers  ${edi_state.rc}        0
    ${edi_state} =               Shell  legionctl --verbose md get
    Should Be Equal As Integers  ${edi_state.rc}        0
    Should not contain           ${edi_state.stdout}    ${md_name}

Run EDI undeploy with version
    [Arguments]           ${enclave}    ${model_id}  ${model_version}
    ${result}=            Run Process without PIPE   legionctl --verbose undeploy ${model_id} --model-version ${model_version} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"     shell=True
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
    [Arguments]           ${model_id}    ${model_version}
    ${resp} =             Shell  legionctl generate-token --model-id ${model_id} --model-version ${model_version}
    Should be equal as integers       ${resp.rc}  0
    Set Suite Variable    ${TOKEN}   ${resp.stdout}

Check model started
    [Documentation]  check if model run in container by http request
    [Arguments]           ${model_id}  ${model_version}
    ${resp}=              Shell  legionctl --verbose model info --model-id ${model_id} --model-version ${model_version}
    Should be equal       ${resp.rc}  ${0}
    Log                   ${resp.stdout}
    Should not be empty   ${resp.stdout}
    [Return]              ${resp.stdout}

Invoke deployed model
    [Documentation]  call model invoke endpoint
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}  ${request_id}=None  ${endpoint}=default  &{arguments}
    ${edge}=              Build enclave EDGE URL    ${enclave}
    ${resp}=              Invoke model API  ${model_id}  ${model_ver}  ${edge}  ${TOKEN}  ${endpoint}  ${request_id}  &{arguments}
    [Return]              ${resp}

Send feedback for deployed model
    [Documentation]  call model feedback endpoint
    [Arguments]           ${enclave}   ${model_id}  ${model_ver}  ${request_id}  &{arguments}
    ${edge}=              Build enclave EDGE URL    ${enclave}
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
    Dictionary Should Contain Key   ${log_entry}  payload
    Dictionary Should Contain Key   ${log_entry}  model_id
    Dictionary Should Contain Key   ${log_entry}  model_version

Validate model feedback log entry Request ID
    [Documentation]  check that model feedback log entry Request ID is correct
    [Arguments]      ${log_entry}   ${excpected_request_id}
    ${actual_request_id}=           Get From Dictionary       ${log_entry}     request_id
    Should Be Equal                 ${actual_request_id}      ${excpected_request_id}

Validate model feedback log entry params
    [Documentation]  check that model feedback log entry params are correct
    [Arguments]      ${log_entry}   &{excpected_values}
    ${actual_payload}=      Get From Dictionary       ${log_entry}          payload
    ${actual_post_args}=    Get From Dictionary       ${actual_payload}     post
    Dictionaries Should Be Equal    ${actual_post_args}    ${excpected_values}

Validate model feedback ID and version
    [Documentation]  check that model feedback ID and version is correct
    [Arguments]      ${log_entry}   ${excpected_model_id}   ${excpected_model_version}
    ${actual_model_id}=            Get From Dictionary       ${log_entry}     model_id
    ${actual_model_version}=       Get From Dictionary       ${log_entry}     model_version
    Should Be Equal                ${actual_model_id}        ${excpected_model_id}
    Should Be Equal                ${actual_model_version}   ${excpected_model_version}

Verify model info from edi
    [Arguments]      ${target_model}       ${model_name}        ${model_state}      ${model_replicas}
    Should Be Equal  ${target_model[0]}    ${model_name}        invalid model name
    Should Be Equal  ${target_model[1]}    ${model_state}       invalid model state
    Should Be Equal  ${target_model[2]}    ${model_replicas}    invalid model replicas

Check if all enclave domains are registered
    [Arguments]             ${enclave}
    :FOR    ${enclave_subdomain}    IN    @{ENCLAVE_SUBDOMAINS}
    \   Check domain exists  ${enclave_subdomain}-${enclave}.${HOST_BASE_DOMAIN}

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
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Get component auth page    ${HOST_PROTOCOL}://${component}.${HOST_BASE_DOMAIN}
    ...    ELSE      Get component auth page    ${HOST_PROTOCOL}://${component}-${enclave}.${HOST_BASE_DOMAIN}
    Log              Auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    Log in

Secured component domain should not be accessible by invalid credentials
    [Arguments]     ${component}    ${enclave}
    [Documentation]  Check that a secured legion component does not provide access by invalid credentials
    &{creds} =       Create Dictionary 	login=admin   password=admin
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Post credentials to auth    ${HOST_PROTOCOL}://${component}    ${HOST_BASE_DOMAIN}    ${creds}
    ...    ELSE      Post credentials to auth    ${HOST_PROTOCOL}://${component}-${enclave}     ${HOST_BASE_DOMAIN}    ${creds}
    Log              Bad auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    Log in to Your Account
    Should contain   ${auth_page}    Invalid Email Address and password

Secured component domain should be accessible by valid credentials
    [Arguments]     ${component}    ${enclave}
    [Documentation]  Check that a secured legion component does not provide access by invalid credentials
    &{creds} =       Create Dictionary    login=${STATIC_USER_EMAIL}    password=${STATIC_USER_PASS}
    &{response} =    Run Keyword If   '${enclave}' == '${EMPTY}'    Post credentials to auth    ${HOST_PROTOCOL}://${component}    ${HOST_BASE_DOMAIN}    ${creds}
    ...    ELSE      Post credentials to auth    ${HOST_PROTOCOL}://${component}-${enclave}     ${HOST_BASE_DOMAIN}    ${creds}
    Log              Bad auth page for ${component} is ${response}
    Dictionary Should Contain Item    ${response}    response_code    200
    ${auth_page} =   Get From Dictionary   ${response}    response_text
    Should contain   ${auth_page}    ${component}
    Should not contain   ${auth_page}    Invalid Email Address and password

Login to the edi and edge
    ${res}=  Shell  legionctl --verbose login --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token "${DEX_TOKEN}"
    Should be equal  ${res.rc}  ${0}
    ${res}=  Shell  legionctl config set MODEL_SERVER_URL ${HOST_PROTOCOL}://edge-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}
    Should be equal  ${res.rc}  ${0}