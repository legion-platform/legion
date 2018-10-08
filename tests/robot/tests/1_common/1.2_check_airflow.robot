*** Settings ***
Documentation       Legion Airflow check
Resource            ../../resources/keywords.robot
Variables           ../../load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}

*** Test Cases ***
Check test dags should not fail
    [Documentation]  Connect to Airflow and check the status of test dags are not failed
    [Tags]  airflow  airflow-api  apps
    :FOR    ${enclave}    IN    @{ENCLAVES}
    \  Invoke and check test dags for valid status code  ${enclave}