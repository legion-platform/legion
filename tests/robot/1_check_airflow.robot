*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils

*** Test Cases ***
Connect to Airflow and check it
    [Documentation]  Connect to Airflow and check status
    [Tags]  airflow  airflow-api
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Airflow     ${enclave}
        ${dags} =                   Find Airflow DAGs
        :FOR    ${dag}   IN   @{dags}
        \   ${tasks} =              Find Airflow Tasks  ${dag}
            :FOR    ${task}     IN      @{tasks}
            \   ${status} =     Trigger Airflow task    ${dag}  ${task}  2018-06-01 00:00:00
                should be equal     ${status}   ${None}
        should not be empty         ${dags}
        ${failed_dags} =            Get failed Airflow DAGs
        should be empty             ${failed_dags}
