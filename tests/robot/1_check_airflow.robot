*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             DateTime

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
            \   ${date_time} =  Get Current Date  result_format='%Y-%m-%d %H:%M:%S'
                ${status} =     Trigger Airflow task    ${dag}  ${task}  ${date_time}
                should be equal     ${status}   ${None}
        should not be empty         ${dags}
        ${failed_dags} =            Get failed Airflow DAGs
        should be empty             ${failed_dags}
