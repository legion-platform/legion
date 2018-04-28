*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ../deploy/profiles/
Library             legion_test.robot.K8s
Library             legion_test.robot.Utils

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Tags]  jenkins  models  enclave
    Connect to Jenkins endpoint
    Run, wait and check jenkins jobs for enclave     ${MODEL_TEST_ENCLAVE}