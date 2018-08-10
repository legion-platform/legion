*** Settings ***
Documentation       Legion stack operational check
Resource            resources/keywords.robot
Variables           load_variables_from_profiles.py   ${PATH_TO_PROFILES_DIR}
Library             legion_test.robot.Utils
Library             legion_test.robot.Jenkins

*** Test Cases ***
Running, waiting and checks jobs in Jenkins
    [Documentation]  Build and check every example in Jenkins
    [Tags]  jenkins  models  enclave
    Sleep    120s
    Connect to Jenkins endpoint
    Run, wait and check jenkins jobs for enclave     ${MODEL_TEST_ENCLAVE}

Check Vertical Scailing
    [Documentation]  Runs "PERF TEST Vertical-Scaling" jenkins job to test vertical scailing
    [Tags]  jenkins model
    
    :FOR  ${enclave}    IN    @{ENCLAVES}
    \  Connect to Jenkins endpoint
        Run Jenkins job                                         PERF TEST Vertical-Scaling   Enclave=${enclave}
        Wait Jenkins job                                        PERF TEST Vertical-Scaling   600
        Last Jenkins job is successful                          PERF TEST Vertical-Scaling
