*** Settings ***
Documentation       Feedback loop (fluentd) check
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             Collections
Library             legion_test.robot.Feedback
Library             legion_test.robot.S3
Library             legion_test.robot.Utils
Library             legion_test.robot.Model
Suite Setup         Run Keywords
...                 Choose cluster context  ${CLUSTER_NAME}   AND
...                 Run EDI deploy and check model started              ${MODEL_TEST_ENCLAVE}   ${TEST_MODEL_IMAGE_4}   ${TEST_FEEDBACK_MODEL_ID}      ${TEST_FEEDBACK_MODEL_VERSION}
Suite Teardown      Run EDI undeploy by model version and check         ${MODEL_TEST_ENCLAVE}   ${TEST_FEEDBACK_MODEL_ID}    ${TEST_FEEDBACK_MODEL_VERSION}   ${TEST_MODEL_IMAGE_4}

*** Variables ***
${REQUEST_ID_CHECK_RETRIES}         100

*** Test Cases ***
Check model API logging without request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - without request ID
    [Tags]  feedback_loop  fluentd  aws  apps
    Choose bucket           ${FEEDBACK__BUCKET}
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  a=${a_value}  b=${b_value}
    Validate model API response      ${response}    result=${expected_response}

    ${request_id}=          Get model API last response ID
    ${meta_log_locations}=       Get S3 paths with lag  ${S3_LOCATION_MODELS_META_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    ${body_log_locations}=             Get S3 paths with lag  ${S3_LOCATION_MODELS_RESP_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}


Check model API logging with request ID and one chunk
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  feedback_loop  fluentd  aws  apps
    Choose bucket           ${FEEDBACK__BUCKET}
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  request_id=${request_id}  a=${a_value}  b=${b_value}
    Validate model API response      ${response}    result=${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=       Get S3 paths with lag  ${S3_LOCATION_MODELS_META_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}

    ${meta_log_entry}=           Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   a=${a_value}  b=${b_value}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    ${body_log_locations}=             Get S3 paths with lag  ${S3_LOCATION_MODELS_RESP_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}

Check model API logging with request ID and many chunks
    [Documentation]  Checking that model API log is being persisted - with specified request ID
    [Tags]  feedback_loop  fluentd  aws  apps
    Choose bucket           ${FEEDBACK__BUCKET}
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${expected_response}=   Repeat string N times    ${TEST_MODEL_ARG_STR}   ${TEST_MODEL_ARG_COPIES}

    ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  request_id=${request_id}  str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}
    Validate model API response      ${response}    result=${expected_response}

    ${actual_request_id}=          Get model API last response ID
    Log                            Response ID is ${actual_request_id}
    Should Be Equal                ${actual_request_id}            ${request_id}

    ${meta_log_locations}=         Get S3 paths with lag  ${S3_LOCATION_MODELS_META_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}

    ${meta_log_entry}=             Find log lines with content   ${meta_log_locations}  ${request_id}  1  ${True}
    Validate model API meta log entry                   ${meta_log_entry}
    Validate model API meta log entry Request ID        ${meta_log_entry}   ${request_id}
    Validate model API meta log entry HTTP method       ${meta_log_entry}   POST
    Validate model API meta log entry POST arguments    ${meta_log_entry}   str=${TEST_MODEL_ARG_STR}  copies=${TEST_MODEL_ARG_COPIES}
    Validate model API meta ID and version              ${meta_log_entry}   ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}

    ${count_of_chunks}=                Get count of invocation chunks from model API meta log entry response   ${meta_log_entry}
    Should Not Be Equal As Integers    ${count_of_chunks}  1
    ${body_log_locations}=             Get S3 paths with lag  ${S3_LOCATION_MODELS_RESP_LOG}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}
    @{response_log_entries}=           Find log lines with content   ${body_log_locations}  ${request_id}  ${count_of_chunks}  ${False}

    Validate model API body log entry for all entries   ${response_log_entries}

    ${aggregated_log_content}=         Get model API body content from all entries  ${response_log_entries}
    Validate model API response        ${aggregated_log_content}    result=${expected_response}

Check model API request generation have no duplicates
    [Documentation]  Checking that model API request generation does not provide same IDs
    [Tags]  feedback_loop  apps
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]
    ${expected_response}=   Convert To Number        ${TEST_MODEL_RESULT}

    ${response_ids}=        Create List

    :FOR    ${i}    IN RANGE    ${REQUEST_ID_CHECK_RETRIES}
    \   ${response}=   Invoke deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  a=${a_value}  b=${b_value}
    \   Validate model API response      ${response}    result=${expected_response}
    \   ${actual_request_id}=          Get model API last response ID
    \   Append To List      ${response_ids}     ${actual_request_id}

    List Should Not Contain Duplicates   ${actual_request_id}


Check model API feedback with request ID
    [Documentation]  Checking that model API feedback is being persisted - without request ID
    [Tags]  feedback_loop  fluentd  aws  apps
    Choose bucket           ${FEEDBACK__BUCKET}
    ${request_id}=          Generate Random String   16  [LETTERS]
    ${a_value}=             Generate Random String   4   [LETTERS]
    ${b_value}=             Generate Random String   4   [LETTERS]

    ${response}=   Send feedback for deployed model    ${MODEL_TEST_ENCLAVE}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${request_id}  a=${a_value}  b=${b_value}
    ${response_status}=     Get From Dictionary         ${response}     status
    Should be true          ${response_status}

    ${log_locations}=       Get S3 paths with lag  ${S3_LOCATION_MODELS_FEEDBACK}  ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}  ${S3_PARTITIONING_PATTERN}

    ${log_entry}=          Find log lines with content   ${log_locations}  ${request_id}  1  ${True}
    Validate model feedback log entry                   ${log_entry}
    Validate model feedback log entry Request ID        ${log_entry}   ${request_id}
    Validate model feedback log entry params            ${log_entry}   a=${a_value}  b=${b_value}
    Validate model feedback ID and version              ${log_entry}   ${TEST_FEEDBACK_MODEL_ID}  ${TEST_FEEDBACK_MODEL_VERSION}