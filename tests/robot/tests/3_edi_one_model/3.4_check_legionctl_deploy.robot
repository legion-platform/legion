*** Settings ***
Documentation       Legion's EDI operational check
Test Timeout        6 minutes
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             Collections
Suite Setup         Choose cluster context  ${CLUSTER_NAME}
Test Setup          Run Keyword And Ignore Error  Run EDI undeploy without version  ${MODEL_TEST_ENCLAVE}  ${TEST_EDI_MODEL_ID}

*** Test Cases ***
Nonexistent image
    [Documentation]  The deploy command must fail if image does not exist
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy nexus-local.cc.epm.kharlamov.biz:443/legion/this-image-does-not:exsit --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Can't get image

Deploy with negative liveness timeout
    [Documentation]  The deploy command must fail if liveness timeout is negative
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --livenesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy with negative readiness timeout
    [Documentation]  The deploy command must fail if readiness timeout is negative
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --readinesstimeout -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             should contain  ${res.stderr}  must be greater than or equal to 0

Deploy with zero replicas
    [Documentation]  The deploy command must fail if number of replicas is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --scale 0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Deploy with negative number of replicas
    [Documentation]  The deploy command must fail if number of replicas is negative
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --scale -3 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be greater then 0

Zero timeout parameter
    [Documentation]  The deploy command must fail if timeout parameter is zero
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --timeout=0 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout parameter
    [Documentation]  The deploy command must fail if it contains negative timeout parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  should be positive integer

Negative timeout with no-wait parameter
    [Documentation]  Ignore negative timeout parameter due to using no-wait parameter
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl --verbose deploy ${TEST_MODEL_IMAGE_3} --no-wait --timeout=-500 --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should be equal  ${res.rc}  ${0}

Missed the host parameter
    [Documentation]  The deploy command must fail if it does not contain an edi host
    [Tags]  edi  cli  enclave
    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_3} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
             Should not be equal  ${res.rc}  ${0}
             Should contain       ${res.stderr}  Failed to connect

# TODO: uncomment after resolving of the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the user parameter
#    [Documentation]  The deploy command must fail if it does not contain an user
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_3} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --password ${SERVICE_PASSWORD}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Missed the password parameter
#    [Documentation]  The deploy command must fail if it does not contain a password
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_3} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT}
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
#
# TODO: uncomment after the issue https://github.com/legion-platform/legion/issues/313 will be completed
#Wrong token
#    [Documentation]  The deploy command must fail if it does not contain a token
#    [Tags]  edi  cli  enclave
#    ${res}=  Shell  legionctl deploy ${TEST_MODEL_IMAGE_3} --edi ${HOST_PROTOCOL}://edi-${MODEL_TEST_ENCLAVE}.${HOST_BASE_DOMAIN} --token wrong-token
#
#             Should not be equal  ${res.rc}  ${0}
#             Should contain       ${res.stderr}  Failed to connect
