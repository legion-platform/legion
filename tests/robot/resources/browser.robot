*** Settings ***
Documentation       Legion robot resources for browser tests
Library             SeleniumLibrary
Library             Collections

*** Variables ***
${BROWSER}            Firefox
${SELENIUM_TIMEOUT}   30 seconds


*** Keywords ***
Open Nexus
    [Arguments]                             ${suburl}
    Open Browser                            ${HOST_PROTOCOL}://nexus.${HOST_BASE_DOMAIN}${suburl}                           ${BROWSER}
    Set Selenium Timeout                    ${SELENIUM_TIMEOUT}

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
    \   Append To List                      ${componentNames}           ${elem.text}
    Return From Keyword  ${componentNames}