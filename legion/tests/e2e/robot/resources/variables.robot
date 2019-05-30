*** Variables ***
@{ENCLAVE_SUBDOMAINS}               edi  edge
@{TEST_MODELS}                      Digit-Recognition  Test-Summation  Sklearn-Income
${MODEL_WITH_PROPS}                 Test-Summation
${MODEL_WITH_PROPS_ENDPOINT}        sum_and_pow
${MODEL_WITH_PROPS_PROP}            number.pow_of_ten
${TEST_MODEL_RESULT}                42.0
${FEEDBACK_TAG}                     tag1
${TEST_MODEL_ARG_COPIES}            3000
${TEST_MODEL_ARG_STR}               test-model-invocation-string__
${S3_LOCATION_MODELS_META_LOG}      model_log/request_response
${S3_LOCATION_MODELS_RESP_LOG}      model_log/response_body
${S3_LOCATION_MODELS_FEEDBACK}      model_log/feedback
${S3_PARTITIONING_PATTERN}          year=%Y/month=%m/day=%d/%Y%m%d%H
${GRAFANA_MAIN_DASHBOARD_UID}       f000cf13-581b-459c-b35e-f5d89fded48f
${TEST_VCS}                         legion
${LEGION_ENTITIES_DIR}              ${CURDIR}/entities