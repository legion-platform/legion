*** Variables ***
${LOCAL_CONFIG}        legion/config_5_1
${TEST_MT_NAME}        stub-model-5-1
${TEST_MD_NAME}        stub-model-5-1
${TEST_MODEL_NAME}     5
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Feedback loop (fluentd) check
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${CLUSTER_PROFILE}
Library             Collections
Library             legion.robot.libraries.feedback.Feedback  ${CLOUD_TYPE}  ${FEEDBACK_BUCKET}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Choose cluster context  ${CLUSTER_CONTEXT}   AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build model  ${TEST_MT_NAME}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  AND
...                 Get token from EDI  ${TEST_MD_NAME}  ${TEST_MD_NAME}  AND
...                 Run EDI deploy and check model started  ${TEST_MD_NAME}  ${TEST_MODEL_IMAGE}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${TEST_MD_NAME}
Suite Teardown      Run Keywords
...                 Delete model training  ${TEST_MT_NAME}  AND
...                 Run EDI undeploy model and check    ${TEST_MD_NAME}
Force Tags          deployment  edi  cli  disable  feedback

*** Variables ***
${REQUEST_ID_CHECK_RETRIES}         30

*** Keywords ***
Invoke deployed model
    [Documentation]  call model invoke endpoint
    [Arguments]           ${md_name}  ${request_id}=None  ${endpoint}=default  &{arguments}
    ${resp}=              Invoke model API  ${md_name}  ${EDGE_URL}  ${TOKEN}  ${endpoint}  ${request_id}  &{arguments}
    [Return]              ${resp}

Send feedback for deployed model
    [Documentation]  call model feedback endpoint
    [Arguments]           ${md_name}  ${model_name}  ${model_ver}  ${request_id}  &{arguments}
    ${resp}=              Invoke model feedback  ${md_name}  ${model_name}  ${model_ver}  ${EDGE_URL}  ${TOKEN}  ${request_id}  &{arguments}
    [Return]              ${resp}

Validate model API meta log entry
    [Documentation]  check that model API log entry contains all required keys
    [Arguments]      ${log_entry}
    Dictionary Should Contain Key   ${log_entry}  request_id
    Dictionary Should Contain Key   ${log_entry}  request_http_method
    Dictionary Should Contain Key   ${log_entry}  request_http_headers
    Dictionary Should Contain Key   ${log_entry}  request_host
    Dictionary Should Contain Key   ${log_entry}  request_uri
    Dictionary Should Contain Key   ${log_entry}  response_http_headers
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

Validate model API meta log entry POST arguments
    [Documentation]  check that model API log entry POST arguments are correct
    [Arguments]      ${log_entry}   &{excpected_values}
    ${actual_post_args}=    Get From Dictionary       ${log_entry}     request_post_args
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
    [Arguments]      ${actual_response}   &{excpected_values}
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
    ${actual_post_args}=    Get From Dictionary       ${actual_payload}     post
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
    Validate model API response      ${response}    result=${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_META_LOG}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}

    ${body_log_locations}=             Get paths with lag  ${FEEDBACK_LOCATION_MODELS_RESP_LOG}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${1}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}

    [Return]  ${meta_log_entry}

*** Test Cases ***
Check model API logging with request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model    ${TEST_MD_NAME}  request_id=${request_id}  a=${a_value}  b=${b_value}

    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}

Check model API logging with request ID and many chunks
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${expected_response}=   Repeat string N times    ${TEST_MODEL_ARG_STR}   ${TEST_MODEL_ARG_COPIES}

    ${response}=   Invoke deployed model    ${TEST_MD_NAME}  endpoint=feedback  request_id=${request_id}  str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}

    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}  str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}

Check model API feedback with request ID
    [Documentation]  Checking that model API feedback is being persisted - without request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]

    Send feedback for deployed model    ${TEST_MD_NAME}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${request_id}  a=${a_value}  b=${b_value}

    ${log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_FEEDBACK}  ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${log_entry}=          Find log lines with content   ${log_locations}  ${request_id}  1  ${True}
    Validate model feedback log entry                   ${log_entry}
    Validate model feedback log entry Request ID        ${log_entry}   ${request_id}
    Validate model feedback ID and version              ${log_entry}   ${TEST_MODEL_NAME}  ${TEST_MODEL_VERSION}
    @{desired_a_values}=    Create List    ${a_value}
    @{desired_b_values}=    Create List    ${b_value}
    Validate model feedback log entry params            ${log_entry}   a=${desired_a_values}  b=${desired_b_values}

Check model API logging without request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - without request ID
    [Tags]  fluentd  aws
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model  ${TEST_MD_NAME}  a=${a_value}  b=${b_value}
    Validate model API response      ${response}    result=${expected_response}

    ${request_id}=          Get model API last response ID
    ${meta_log_entry}=  Validate model feedback  ${request_id}  ${response}  ${expected_response}
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}
