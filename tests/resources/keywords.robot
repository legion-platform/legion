*** Settings ***
Documentation       Legion robot resources
Library             String
Library             OperatingSystem
Library             Collections
Library             legion_test.robot.Dashboard
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Utils
Library             legion_test.robot.Grafana

*** Keywords ***
Connect to endpoints
    Connect to Jenkins    ${HOST_PROTOCOL}://jenkins.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}
    Connect to Grafana    ${HOST_PROTOCOL}://grafana.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}

Run EDI inspect
    ${edi_state}=   Run      legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                      EDI returns ${edi_state}
    [Return]        ${edi_state}

Connect to kubernetes
    Gather kubernetes dashboard info                        ${HOST_PROTOCOL}://dashboard.${HOST_BASE_DOMAIN}          ${CLUSTER_NAMESPACE}

Test model pipeline
    [Arguments]              ${model_name}
    Run Jenkins job                                         DYNAMIC MODEL ${model_name}
    Wait Jenkins job                                        DYNAMIC MODEL ${model_name}   600
    Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}
    Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    Log                  Model meta is ${model_meta}
    ${model_path} =      Get From Dictionary                ${model_meta}                 modelPath
    ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    ${model_path} =	     Get Regexp Matches	                ${model_path}                 (.*)://[^/]+/(?P<path>.*)   path
    ${model_url} =       Set Variable                       ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}/${model_path[0]}
    Log                  External model URL is ${model_url}
    Check remote file exists                                ${model_url}                  ${SERVICE_ACCOUNT}          jonny
    Dashboard should exists                                 ${model_id}
    Sleep                15s
    Metric should be presented                              ${model_id}
    ${edi_state}=        Run      legionctl inspect --filter ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                  State of ${model_id} is ${edi_state}