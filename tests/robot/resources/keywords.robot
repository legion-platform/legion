*** Settings ***
Documentation       Legion robot resources
Resource            variables.robot
Library             String
Library             OperatingSystem
Library             Collections
Library             legion_test.robot.K8s
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Utils
Library             legion_test.robot.Grafana
Library             legion_test.robot.Airflow

*** Keywords ***
Connect to enclave Grafana
    [Arguments]           ${enclave}
    Connect to Grafana    ${HOST_PROTOCOL}://grafana-${enclave}.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}

Connect to Jenkins endpoint
    Connect to Jenkins    ${HOST_PROTOCOL}://jenkins.${HOST_BASE_DOMAIN}                                 ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}

Connect to enclave Airflow
    [Arguments]           ${enclave}
    Connect to Airflow    ${HOST_PROTOCOL}://airflow-${enclave}.${HOST_BASE_DOMAIN}

Connect to enclave Flower
    [Arguments]           ${enclave}
    Connect to Flower    ${HOST_PROTOCOL}://flower-${enclave}.${HOST_BASE_DOMAIN}


Run EDI inspect
    [Arguments]           ${enclave}
    ${edi_state}=   Run   legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Run EDI inspect with parse
    [Arguments]           ${enclave}
    ${edi_state} =        Run EDI inspect                                ${enclave}
    ${parsed} =           Parse edi inspect columns info                 ${edi_state}
    [Return]              ${parsed}

Run EDI deploy
    [Arguments]           ${enclave}    ${image}
    ${edi_state} =  Run   legionctl deploy ${image} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Run EDI undeploy with version
    [Arguments]           ${enclave}    ${model_id}  ${model_version}
    ${edi_state} =  Run   legionctl undeploy ${model_id} --model-version ${model_version} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Run EDI undeploy without version
    [Arguments]           ${enclave}    ${model_id}
    ${edi_state} =  Run   legionctl undeploy ${model_id} --ignore-not-found --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Run EDI scale
    [Arguments]           ${enclave}    ${model_id}     ${new_scale}
    ${edi_state} =  Run   legionctl scale ${model_id} ${new_scale} --edi ${HOST_PROTOCOL}://edi-${enclave}.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                   EDI returns ${edi_state}
    [Return]              ${edi_state}

Test model pipeline
    [Arguments]          ${model_name}                      ${enclave}=${CLUSTER_NAMESPACE}
    Run Jenkins job                                         DYNAMIC MODEL ${model_name}   Enclave=${enclave}
    Wait Jenkins job                                        DYNAMIC MODEL ${model_name}   600
    Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    Log                  Model meta is ${model_meta}
    ${model_path} =      Get From Dictionary                ${model_meta}                 modelPath
    ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    ${model_version} =   Get From Dictionary                ${model_meta}                 modelVersion
    ${model_path} =	     Get Regexp Matches	                ${model_path}                 (.*)://[^/]+/(?P<path>.*)   path
    ${model_url} =       Set Variable                       ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}/${model_path[0]}
    Log                  External model URL is ${model_url}
    Check remote file exists                                ${model_url}                  ${SERVICE_ACCOUNT}          jonny
    Connect to enclave Grafana                              ${enclave}
    Dashboard should exists                                 ${model_id}
    Sleep                15s
    Metric should be presented                              ${model_id}                   ${model_version}
    ${edi_state}=        Run      legionctl inspect --filter ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                  State of ${model_id} is ${edi_state}

Check if all enclave domains are registered
    [Arguments]             ${enclave}
    :FOR    ${enclave_subdomain}    IN    @{ENCLAVE_SUBDOMAINS}
    \   Check domain exists  ${enclave_subdomain}-${enclave}.${HOST_BASE_DOMAIN}

Run, wait and check jenkins jobs for enclave
    [Arguments]             ${enclave}
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
    \    Test model pipeline  ${model_name}  ${enclave}