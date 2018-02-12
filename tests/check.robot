*** Settings ***
Documentation       Legion stack operational check
Library             String
Library             OperatingSystem
Library             Collections
Library             legion_test.robot.Dashboard
Library             legion_test.robot.Jenkins
Library             legion_test.robot.Utils
Library             legion_test.robot.Grafana

*** Variables ***
${HOST_PROTOCOL}           http
${DASHBOARD_PROTOCOL}      https
${HOST_BASE_DOMAIN}        k8s-nightly.epm.kharlamov.biz
${CLUSTER_NAMESPACE}       default
@{LIST_SUBDOMAINS}         edi  dashboard  nexus  grafana  ldap
@{LIST_JENKINS_JOBS}       Test-Summation  Sklearn-Income  Digit-Recognition
${SERVICE_ACCOUNT}         admin
${SERVICE_PASSWORD}        admin
${DEPLOYMENT}              legion

*** Test Cases ***
Checking all domains have been registered
    :FOR    ${subdomain}    IN    @{LIST_SUBDOMAINS}
    \   Check domain exists  ${subdomain}.${HOST_BASE_DOMAIN}

Checking all replica sets, stateful sets, replication controllers are up and running
    Gather kubernetes dashboard info         ${DASHBOARD_PROTOCOL}://dashboard.${HOST_BASE_DOMAIN}    ${CLUSTER_NAMESPACE}
    Replica set is running                   hub
    Replica set is running                   ${DEPLOYMENT}-nexus
    Replica set is running                   proxy
    Stateful set is running                  ${DEPLOYMENT}-consul
    Replication controller is running        ${DEPLOYMENT}-edge
    Replication controller is running        ${DEPLOYMENT}-edi
    Replication controller is running        ${DEPLOYMENT}-grafana
    Replication controller is running        ${DEPLOYMENT}-graphite
    Replication controller is running        ${DEPLOYMENT}-jenkins
    Replication controller is running        ${DEPLOYMENT}-ldap-gui
    Replication controller is running        ${DEPLOYMENT}-ldap-server

Checking legionctl can connect to cluster
    ${edi_state}=   Run      legionctl inspect --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    Log                      EDI returns ${edi_state}
    Should not contain       ${edi_state}   legionctl: error
    Should not contain       ${edi_state}   Exception

Running, waiting and checks jobs in Jenkins
    Connect to Jenkins    ${HOST_PROTOCOL}://jenkins.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}
    Connect to Grafana    ${HOST_PROTOCOL}://grafana.${HOST_BASE_DOMAIN}                      ${SERVICE_ACCOUNT}          ${SERVICE_PASSWORD}
    :FOR  ${model_name}  IN  @{LIST_JENKINS_JOBS}
    \   Run Jenkins job                                         DYNAMIC MODEL ${model_name}
    \   Wait Jenkins job                                        DYNAMIC MODEL ${model_name}   600
    \   Last Jenkins job is successful                          DYNAMIC MODEL ${model_name}
    \   Jenkins artifact present                                DYNAMIC MODEL ${model_name}   notebook.html
    \   ${model_meta} =      Jenkins log meta information       DYNAMIC MODEL ${model_name}
    \   Log                  Model meta is ${model_meta}
    \   ${model_path} =      Get From Dictionary                ${model_meta}                 modelPath
    \   ${model_id} =        Get From Dictionary                ${model_meta}                 modelId
    \   ${model_path} =	     Get Regexp Matches	                ${model_path}                 (.*)://[^/]+/(?P<path>.*)   path
    \   ${model_url} =       Set Variable                       ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}/${model_path[0]}
    \   Log                  External model URL is ${model_url}
    \   Check remote file exists                                ${model_url}                  ${SERVICE_ACCOUNT}          jonny
    \   Dashboard should exists                                 ${model_id}
    \   Metric should be presented                              ${model_id}
    \   ${edi_state}=        Run      legionctl inspect --filter ${model_id} --format column --edi ${HOST_PROTOCOL}://edi.${HOST_BASE_DOMAIN} --user ${SERVICE_ACCOUNT} --password ${SERVICE_PASSWORD}
    \   Log                  State of ${model_id} is ${edi_state}

