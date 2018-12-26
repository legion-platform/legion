*** Variables ***
@{SUBDOMAINS}                       jenkins  nexus
@{ENCLAVE_SUBDOMAINS}               edi  edge  airflow  flower
@{TEST_DAGS}                        example_python_work  s3_connection_test
${MODEL_WITH_PROPS}                 Test-Summation
${MODEL_WITH_PROPS_ENDPOINT}        sum_and_pow
${MODEL_WITH_PROPS_PROP}            number.pow_of_ten
${TEST_MODEL_ID}                    demo-abc-model
${TEST_EDI_MODEL_ID}                edi-test-model
${TEST_COMMAND_MODEL_ID}            command-test-model
${TEST_FEEDBACK_MODEL_ID}           feedback-test-model
${TEST_FEEDBACK_MODEL_VERSION}      1.0
${TEST_MODEL_1_VERSION}             1.0
${TEST_MODEL_2_VERSION}             1.1
${TEST_MODEL_3_VERSION}             1.2
${TEST_MODEL_5_VERSION}             1.0
${TEST_MODEL_6_ID}                  auth-test-model
${TEST_MODEL_6_VERSION}             1.0
${TEST_MODEL_VERSION}               1.0
${TEST_MODEL_RESULT}                42.0
${FEEDBACK_TAG}                     tag1
${TEST_MODEL_ARG_COPIES}            3000
${TEST_MODEL_ARG_STR}               test-model-invocation-string__
${S3_LOCATION_MODELS_META_LOG}      model_log/request_response
${S3_LOCATION_MODELS_RESP_LOG}      model_log/response_body
${S3_LOCATION_MODELS_FEEDBACK}      model_log/feedback
${S3_PARTITIONING_PATTERN}          year=%Y/month=%m/day=%d/%Y%m%d%H
# TODO: Two next lines should be removed when closing LEGION #499, #313, #316
${SERVICE_ACCOUNT}                  admin
${SERVICE_PASSWORD}                 admin