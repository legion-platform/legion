*** Variables ***
${LOCAL_CONFIG}        legion/config_5_1
${TEST_MODEL_NAME}     stub-model-5-1
${TEST_MODEL_ID}       5
${TEST_MODEL_VERSION}  1

*** Settings ***
Documentation       Feedback loop (fluentd) check
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion.robot.libraries.feedback.Feedback  ${CLOUD_TYPE}  ${FEEDBACK_BUCKET}
Library             legion.robot.libraries.utils.Utils
Library             legion.robot.libraries.model.Model
Suite Setup         Run Keywords
...                 Choose cluster context  ${CLUSTER_NAME}   AND
...                 Set Environment Variable  LEGION_CONFIG  ${LOCAL_CONFIG}  AND
...                 Login to the edi and edge  AND
...                 Build stub model  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Get token from EDI  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Run EDI deploy and check model started  ${TEST_MODEL_NAME}   ${TEST_MODEL_IMAGE}   ${TEST_MODEL_ID}    ${TEST_MODEL_VERSION}
Suite Teardown      Run Keywords
...                 Delete stub model training  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  AND
...                 Run EDI undeploy model without version and check    ${TEST_MODEL_NAME}
Force Tags          feedback_loop  apps

*** Variables ***
${REQUEST_ID_CHECK_RETRIES}         30

*** Test Cases ***
Check model API logging without request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - without request ID
    [Tags]  fluentd  aws
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  a=${a_value}  b=${b_value}
    Validate model API response      ${response}    result=${expected_response}

    ${request_id}=          Get model API last response ID
    ${meta_log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_META_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    ${body_log_locations}=             Get paths with lag  ${FEEDBACK_LOCATION_MODELS_RESP_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}


Check model API logging with request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  request_id=${request_id}  a=${a_value}  b=${b_value}
    Validate model API response      ${response}    result=${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_META_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    ${body_log_locations}=             Get paths with lag  ${FEEDBACK_LOCATION_MODELS_RESP_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}

Check model API logging with request ID and many chunks
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${expected_response}=   Repeat string N times    ${TEST_MODEL_ARG_STR}   ${TEST_MODEL_ARG_COPIES}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  endpoint=feedback  request_id=${request_id}  str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}
    Validate model API response      ${response}    result=${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=         Get paths with lag  ${FEEDBACK_LOCATION_MODELS_META_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${meta_log_entry}=             Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    Should Not Be Equal As Integers    ${count_of_chunks}  1
    ${body_log_locations}=             Get paths with lag  ${FEEDBACK_LOCATION_MODELS_RESP_LOG}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}

Check model API request generation have no duplicates
    [Documentation]  Checking that model API request generation does not provide same IDs
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response_ids}=        Create List

    :FOR    ${i}    IN RANGE    ${REQUEST_ID_CHECK_RETRIES}
    \   ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  a=${a_value}  b=${b_value}
    \   Validate model API response      ${response}    result=${expected_response}
    \   ${actual_request_id}=          Get model API last response ID
    \   Append To List      ${response_ids}     ${actual_request_id}

    List Should Not Contain Duplicates   ${response_ids}


Check model API feedback with request ID
    [Documentation]  Checking that model API feedback is being persisted - without request ID
    [Tags]  fluentd  aws
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]

    ${response}=   Send feedback for deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${request_id}  a=${a_value}  b=${b_value}
    ${response_error}=      Get From Dictionary         ${response}     error
    Should Not Be True      ${response_error}

    ${log_locations}=       Get paths with lag  ${FEEDBACK_LOCATION_MODELS_FEEDBACK}  ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}  ${FEEDBACK_PARTITIONING_PATTERN}

    ${log_entry}=          Find log lines with content   ${log_locations}  ${request_id}  1  ${True}
    Validate model feedback log entry                   ${log_entry}
    Validate model feedback log entry Request ID        ${log_entry}   ${request_id}
    Validate model feedback ID and version              ${log_entry}   ${TEST_MODEL_ID}  ${TEST_MODEL_VERSION}
    @{desired_a_values}=    Create List    ${a_value}
    @{desired_b_values}=    Create List    ${b_value}
    Validate model feedback log entry params            ${log_entry}   a=${desired_a_values}  b=${desired_b_values}