*** Settings ***
Documentation       Legion stack operational check
Resource            ../../resources/keywords.robot
Resource            ../../resources/variables.robot
Variables           ../../load_variables_from_profiles.py    ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.K8s
Library             legion_test.robot.Flower
Library             legion_test.robot.Utils
Test Setup          Choose cluster context            ${CLUSTER_NAME}
Default Tags        airflow  flower  scale  apps

*** Test Cases ***
Check if flower available
    [Documentation]  Check if Flower UI is available
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Flower     ${enclave}
        Check if flower online

Check if flower scale up works properly
    [Documentation]  Scale up Flower deployment and check if number of celery workers increases
    [Setup]  Set replicas num   ${1}
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Flower     ${enclave}
       Wait for worker is ready    expected_count=${1}
       ${workers_number} =           Get number of workers from Flower
       ${replicas_number} =          Get deployment replicas     airflow-${enclave}-worker  ${enclave}
       Should be equal as integers   ${workers_number}  ${replicas_number}  Workers number doesn't equal to     Replicas number
       ${new_replicas_number} =      Sum up   ${replicas_number}  ${1}
       Set deployment replicas       ${new_replicas_number}  airflow-${enclave}-worker  ${enclave}
       Wait deployment replicas count   airflow-${enclave}-worker  namespace=${enclave}  expected_replicas_num=${new_replicas_number}
       ${replicas_number} =          Get deployment replicas     airflow-${enclave}-worker  ${enclave}
       Wait for worker is ready    expected_count=${new_replicas_number}
       ${workers_number} =           Get number of workers from Flower
       Should be equal as integers   ${new_replicas_number}  ${replicas_number}  Actual Replicas values doens't equal    to set Replicas number
       Should be equal as integers   ${new_replicas_number}  ${workers_number}   Workers number hasn't been increased    to new Replicas number

Check if flower scale down works properly
    [Documentation]  Scale down Flower deployment and check if number of celery workers decreases
    [Setup]  Set replicas num   ${2}
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Flower     ${enclave}
       Wait for worker is ready  expected_count=${2}
       ${workers_number} =           Get number of workers from Flower
       ${replicas_number} =          Get deployment replicas   airflow-${enclave}-worker  ${enclave}
       Should be equal as integers   ${workers_number}  ${replicas_number}  Workers number doesn't equal to     Replicas number
       ${new_replicas_number} =      Subtract   ${replicas_number}  ${1}
       Set deployment replicas       ${new_replicas_number}  airflow-${enclave}-worker  ${enclave}
       Wait deployment replicas count   airflow-${enclave}-worker  namespace=${enclave}  expected_replicas_num=${new_replicas_number}
       ${replicas_number} =          Get deployment replicas   airflow-${enclave}-worker  ${enclave}
       Wait for worker is ready   expected_count=${new_replicas_number}
       ${workers_number} =           Get number of workers from Flower
       Should be equal as integers   ${new_replicas_number}  ${workers_number}   Actual Replicas values doens't equal    to set Replicas number
       Should be equal as integers   ${new_replicas_number}  ${replicas_number}  Workers number hasn't been decreased to new Replicas number
