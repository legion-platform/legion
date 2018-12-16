*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Choose cluster context  ${CLUSTER_NAME}

*** Test Cases ***
Missed the host parameter
    [Documentation]  The inspect command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl inspect --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the user parameter
#    [Documentation]  The inspect command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the password parameter
#    [Documentation]  The inspect command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Wrong token
#    [Documentation]  The inspect command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl inspect --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
