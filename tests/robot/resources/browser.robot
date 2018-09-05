*** Settings ***
Documentation       Legion robot resources for browser tests
Library             SeleniumLibrary
Library             Collections

*** Variables ***
${BROWSER}            Firefox
${SELENIUM_TIMEOUT}   30 seconds
${NEXUS_HOST}         ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}

#   LOCATORS
##  DEX AUTH PAGE
${DEX_AUTH_dex_email_login_button}   //button[contains(@class, 'dex-btn theme-btn-provider')]
${DEX_AUTH_login_input}              //*[@id="login"]
${DEX_AUTH_password_input}           //*[@id="password"]
${DEX_AUTH_login_button}             //*[@id="submit-login"]

*** Keywords ***
Start browser
    [Arguments]                             ${url}
    Open Browser                            ${url}                           ${BROWSER}
    Set Selenium Timeout                    ${SELENIUM_TIMEOUT}

Login with dex
    Wait Until Element Is Visible           xpath: ${DEX_AUTH_dex_email_login_button}
    Click Button                            xpath: ${DEX_AUTH_dex_email_login_button}
    Wait Until Element Is Visible           xpath: ${DEX_AUTH_login_input}
    Input Text 	                            xpath: ${DEX_AUTH_login_input} 	    ${STATIC_USER_EMAIL}
    Input Text 	                            xpath: ${DEX_AUTH_password_input} 	${STATIC_USER_PASS}
    Click Button                            xpath: ${DEX_AUTH_login_button}

Wait Nexus componens in menu
    Wait Until Element Is Visible           xpath: //span[contains(@class, 'x-tree-node-text') and contains(text(), "Components")]

Wait Nexus components table
    Wait Until Element Is Visible           xpath: //label[contains(text(), "Browse components and assets")]
    Wait Until Element Is Visible           xpath: //button/i[contains(@class, "fa-clipboard")]
    Sleep                                   3 seconds

Get Nexus components table
    @{components}=       Get WebElements    xpath: //label[contains(text(), "Components")]/ancestor::div[contains(concat(" ", @class, " "), " nx-feature-content ")]//table//tr/td[2]/div[contains(@class, "x-grid-cell-inner")]
    ${componentNames}=   Create List
    :FOR    ${elem}    IN    @{components}
    \   Append To List                      ${componentNames}    ${elem.text}
    Return From Keyword  ${componentNames}