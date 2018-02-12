*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ../deploy/profiles/
Library             legion_test.robot.Dashboard
Library             legion_test.robot.Utils

*** Test Cases ***
Checking all domains have been registered
    [Documentation]  Check that all required DNS A records has been registered
    :FOR    ${subdomain}    IN    @{SUBDOMAINS}
    \   Check domain exists  ${subdomain}.${REAL_HOST_BASE_DOMAIN}

Checking all replica sets, stateful sets, replication controllers are up and running
    [Documentation]  Gather information from kubernetes through dashboard and check state of all required componens
    Connect to kubernetes
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

Connecting to endpoins (EDI, Jenkins, Grafana)
    [Documentation]  Try to connect to EDI, Jenkins, Grafana and check connection
    Connect to endpoints
    ${edi_state} =           Run EDI inspect
    Should not contain       ${edi_state}   legionctl: error
    Should not contain       ${edi_state}   Exception

Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    :FOR  ${model_name}  IN  @{JENKINS_JOBS}
    \   Test model pipeline  ${model_name}
