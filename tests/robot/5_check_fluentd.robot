*** Settings ***
Documentation       Feedback loop (fluentd) check
Resource            resources/keywords.robot
Resource            resources/variables.robot
Variables           load_variables_from_profiles.py   ../../deploy/profiles/
Library             Collections
Library             legion_test.robot.Feedback
Library             legion_test.robot.S3
Library             legion_test.robot.Utils

*** Test Cases ***
Check feedback gathering
    [Documentation]  Checking that feedback gathering works
    [Tags]  feedback  fluentd
    Send feedback data      ${HOST_PROTOCOL}://feedback-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}   ${feedback_tag}  a=0

Check feedback processing
    [Documentation]  Checking that feedback process works normally
    [Tags]  feedback  fluentd  aws
    Choose bucket           ${FEEDBACK__BUCKET}

    ${a_value} =            Generate Random String   4                  [NUMBERS]
    ${event_time} =         Wait up to second        20                 year=%Y/month=%m/day=%d/%Y%m%d%H
    Send feedback data      ${HOST_PROTOCOL}://feedback-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN}   ${feedback_tag}  a=${a_value}
    Wait up to second       19

    ${file_prefix} =        Join bucket paths        ${feedback_prefix}    ${feedback_tag}    ${event_time}

    ${files} =              Get files in bucket      ${file_prefix}
    Log list                ${files}
    ${last} =	            Get From List	         ${files}	        -1

    Check file exists in bucket                      ${last}
    ${data} =               Get file content from bucket    ${last}

    Should Contain          ${data}                 {"a":"${a_value}"}




