*** Settings ***
Documentation       Legion robot resources for browser tests
Library             Selenium2Library
Library             Collections

*** Variables ***
${BROWSER}                  Firefox
${SELENIUM_TIMEOUT}         60 seconds    #time to explicite wait for keywords run
${SELENIUM_IMPLICIT_WAIT}   5 seconds     #time to wait for a DOM load on page
${NEXUS_COMPONENTS_TABLE}   //table[contains(.,'docker')]


*** Keywords ***
Start browser
    [Arguments]                  ${url}
    Open Browser                 ${url}                     ${BROWSER}
    Set Selenium Timeout         ${SELENIUM_TIMEOUT}
    Set Selenium Implicit Wait   ${SELENIUM_IMPLICIT_WAIT}
    Maximize Browser Window

Login with dex
     Wait Until Element Is Visible           xpath: ${DEX_AUTH_dex_email_login_button}
     Click Button                            xpath: ${DEX_AUTH_dex_email_login_button}
     Wait Until Element Is Visible           xpath: ${DEX_AUTH_login_input}
     Input Text 	                            xpath: ${DEX_AUTH_login_input} 	    ${STATIC_USER_EMAIL}
     Input Text 	                            xpath: ${DEX_AUTH_password_input} 	${STATIC_USER_PASS}
     Click Button                            xpath: ${DEX_AUTH_login_button}

Wait Nexus componens in menu
    Wait Until Element Is Visible   xpath: //span[contains(@class, 'x-tree-node-text') and contains(text(), "Components")]

Check components presence in Nexus table
    [Arguments]  ${list_of_components}
    Wait Until Page Contains Element  ${NEXUS_COMPONENTS_TABLE}
    Wait Until Element Is Visible   ${NEXUS_COMPONENTS_TABLE}
    :FOR  ${item}  IN  @{list_of_components}
    \  Wait Until Page Contains Element  ${NEXUS_COMPONENTS_TABLE}
    \  Wait Until Element Is Visible   ${NEXUS_COMPONENTS_TABLE}
    \  Table Should Contain   ${NEXUS_COMPONENTS_TABLE}  ${item}
