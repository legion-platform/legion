*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ../../deploy/profiles/
Library             legion_test.robot.Utils

*** Test Cases ***
Connect to Airflow and check it
    [Documentation]  Connect to Airflow and check status
    [Tags]  airflow  airflow-api
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Airflow     ${enclave}
        ${dags} =                   Find Airflow DAGs
        Should not be empty         ${dags}
        ${failed_dags} =            Get failed Airflow DAGs
        should be empty             ${failed_dags}
