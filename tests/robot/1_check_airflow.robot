*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             DateTime

*** Test Cases ***
Check test dags should not fail
    [Documentation]  Connect to Airflow and check the status of test dags are not failed
    [Tags]  airflow  airflow-api
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Connect to enclave Airflow     ${enclave}
    \  keywords.Check Test Dags For Valid Status Code   ${TEST_DAGS}
    should not be empty         ${TEST_DAGS}
    ${failed_dags} =            Get failed Airflow DAGs
    Should Not Contain          ${failed_dags}    example_python_work
    Should Not Contain          ${failed_dags}    s3_connection_test