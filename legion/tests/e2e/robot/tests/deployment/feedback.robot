*** Variables ***
${RES_DIR}             ${CURDIR}/resources
${LOCAL_CONFIG}        legion/config_deployment_feedback
${MD_FEEDBACK_MODEL}   feedback-model
${TEST_MODEL_NAME}     feedback
${TEST_MODEL_VERSION}  5.5

*** Settings ***
Documentation       Feedback loop (fluentd) check
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Library             legion.robot.libraries.feedback.Feedback  ${CLOUD_TYPE}  ${FEEDBACK_BUCKET}  ${CLUSTER_NAME}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Cleanup resources  AND
...                 Run EDI deploy from model packaging  ${MP_FEEDBACK_MODEL}  ${MD_FEEDBACK_MODEL}  ${RES_DIR}/simple-model.deployment.legion.yaml  AND
...                 Check model started  ${MD_FEEDBACK_MODEL}
Suite Teardown      Run keywords  Cleanup resources  AND
...                 Remove File  ${LOCAL_CONFIG}
Force Tags          deployment  edi  cli  feedback

*** Variables ***
${REQUEST_ID_CHECK_RETRIES}         30
@{FORBIDDEN_HEADERS}  authorization  x-jwt  x-user  x-email

*** Keywords ***
Cleanup resources
    StrictShell  legionctl --verbose dep delete --id ${MD_FEEDBACK_MODEL} --ignore-not-found

Invoke deployed model
    [Documentation]  call model invoke endpoint
    [Arguments]           ${md_name}  ${request_id}=${NONE}  &{arguments}
    ${resp}=              Invoke model API  ${md_name}  ${EDGE_URL}  ${AUTH_TOKEN}  ${request_id}  &{arguments}
    [Return]              ${resp}

Send feedback for deployed model
    [Documentation]  call model feedback endpoint
    [Arguments]           ${md_name}  ${model_name}  ${model_ver}  ${request_id}  &{arguments}
    ${resp}=              Invoke model feedback  ${md_name}  ${model_name}  ${model_ver}  ${EDI_URL}  ${AUTH_TOKEN}  ${request_id}  &{arguments}
    [Return]              ${resp}

Validate model API meta log entry
    [Documentation]  check that model API log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  request_http_method
    Dictionary Should Contain Key   ${log_entry}  request_http_headers
    Dictionary Should Contain Key   ${log_entry}  request_host
    Dictionary Should Contain Key   ${log_entry}  request_uri
    Dictionary Should Contain Key   ${log_entry}  response_status
    Dictionary Should Contain Key   ${log_entry}  model_name
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

Validate model API meta log entry HTTP headers
    [Documentation]  check that model API log entry HTTP headers do not have a forbidden header
    [Arguments]      ${log_entry}
    ${request_http_headers}=                 Get From Dictionary       ${log_entry}     request_http_headers

    FOR    ${header}    IN    @{FORBIDDEN_HEADERS}
        Dictionary should not contain key  ${request_http_headers}  ${header}
    END

Validate model API meta log entry POST arguments
    [Documentation]  check that model API log entry POST arguments are correct
    [Arguments]      ${log_entry}   ${excpected_values}
    ${actual_post_args}=    Get From Dictionary       ${log_entry}     request_content
    ${actual_post_args}=    Evaluate     json.loads("""${actual_post_args}""")    json
    Dictionaries Should Be Equal    ${actual_post_args}    ${excpected_values}

Validate model API meta ID and version
    [Documentation]  check that model API ID and version is correct
    [Arguments]      ${log_entry}   ${excpected_model_name}   ${excpected_model_version}
    ${actual_model_name}=            Get From Dictionary       ${log_entry}     model_name
    ${actual_model_version}=       Get From Dictionary       ${log_entry}     model_version
    Should Be Equal                ${actual_model_name}        ${excpected_model_name}
    Should Be Equal                ${actual_model_version}   ${excpected_model_version}

Validate model API response
    [Documentation]  check that model API response is correct
    [Arguments]      ${actual_response}   ${excpected_values}
    Dictionaries Should Be Equal    ${actual_response}    ${excpected_values}

Validate model API body log entry
    [Documentation]  check that model API body log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  response_content
    Dictionary Should Contain Key   ${log_entry}  model_name
    Dictionary Should Contain Key   ${log_entry}  model_version

Validate model API body log entry for all entries
    [Documentation]  check that model API body log entries contains all required keys
    [Arguments]      ${log_entries}
    :FOR    ${log_entry}    IN    @{log_entries}
    \    Validate model API body log entry    ${log_entry}

Get model API body content from all entries
    [Documentation]  get model API body content from all entries
    [Arguments]      ${log_entries}
    ${content}=              Concatinate list of dicts field  ${log_entries}  response_content
    Log                      ${content}
    ${parsed_content}=       Parse JSON string  ${content}
    [Return]  ${parsed_content}

Validate model feedback log entry
    [Documentation]  check that model feedback log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  payload
    Dictionary Should Contain Key   ${log_entry}  model_name
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
    ${actual_post_args}=    Get From Dictionary       ${actual_payload}     json
    Dictionaries Should Be Equal    ${actual_post_args}    ${excpected_values}

Validate model feedback ID and version
    [Documentation]  check that model feedback ID and version is correct
    [Arguments]      ${log_entry}   ${excpected_model_name}   ${excpected_model_version}
    ${actual_model_name}=            Get From Dictionary       ${log_entry}     model_name
    ${actual_model_version}=       Get From Dictionary       ${log_entry}     model_version
    Should Be Equal                ${actual_model_name}        ${excpected_model_name}
    Should Be Equal                ${actual_model_version}   ${excpected_model_version}

Validate model feedback
    [Arguments]  ${request_id}  ${response}  ${expected_response}
    [Documentation]  check model feedback
    Validate model API response      ${response}    ${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_META_LOG}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}
    Validate model API meta log entry HTTP headers      ${meta_log_entry}

    ${body_log_locations}=             Get paths with lag  ${FEEDBACK_LOCATION_MODELS_RESP_LOG}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${1}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    ${expected_response}

    [Return]  ${meta_log_entry}

*** Test Cases ***
Check model API logging with request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${str}=                 Generate Random String   4   [LETTERS]
    ${copies}=              set variable  ${4}
    ${expected_request}=    evaluate  {'data': [['${str}', ${copies}]], 'columns': ['str', 'copies']}
    ${expected_response}=   evaluate  {'prediction': [['${str}' * int(${copies})]], 'columns': ['result']}

    ${response}=   Invoke deployed model    ${MD_FEEDBACK_MODEL}  request_id=${request_id}  str=${str}  copies=${copies}

    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}   ${expected_request}

Check model API logging with request ID and many chunks
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${expected_request}=    evaluate  {'data': [['${TEST_MODEL_ARG_STR}', ${TEST_MODEL_ARG_COPIES}]], 'columns': ['str', 'copies']}
    ${expected_response}=   evaluate  {'prediction': [['${TEST_MODEL_ARG_STR}' * int(${TEST_MODEL_ARG_COPIES})]], 'columns': ['result']}

    ${response}=   Invoke deployed model    ${MD_FEEDBACK_MODEL}  request_id=${request_id}  str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}

    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}  ${expected_request}

Check model API feedback with request ID
    [Documentation]  Checking that model API feedback is being persisted - without request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${str}=                 Generate Random String   4   [LETTERS]
    ${copies}=              set variable  ${4.0}

    Send feedback for deployed model    ${MD_FEEDBACK_MODEL}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${request_id}  str=${str}  copies=${copies}

    ${log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_FEEDBACK}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${log_entry}=          Find log lines with content   ${log_locations}  ${request_id}  1  ${True}
    Validate model feedback log entry                   ${log_entry}
    Validate model feedback log entry Request ID        ${log_entry}   ${request_id}
    Validate model feedback ID and version              ${log_entry}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}

    Validate model feedback log entry params            ${log_entry}   str=${str}  copies=${copies}

Check model API logging without request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - without request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${str}=                 Generate Random String   4   [LETTERS]
    ${copies}=              set variable  ${4}
    ${expected_request}=   evaluate  {'data': [['${str}', ${copies}]], 'columns': ['str', 'copies']}
    ${expected_response}=   evaluate  {'prediction': [['${str}' * int(${copies})]], 'columns': ['result']}

    ${response}=   Invoke deployed model  ${MD_FEEDBACK_MODEL}  str=${str}  copies=${copies}
    Validate model API response      ${response}    ${expected_response}

    ${request_id}=          Get model API last response ID
    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}   ${expected_request}
