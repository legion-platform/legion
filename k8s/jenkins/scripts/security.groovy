#!groovy
/**
 *   Copyright 2017 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

import jenkins.model.*
import hudson.security.*
import jenkins.security.s2m.AdminWhitelistRule
import hudson.model.*
import hudson.tools.*
import hudson.plugins.*
import hudson.security.SecurityRealm.*
import org.jenkinsci.plugins.oic.*
 
def instance = Jenkins.getInstance()
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def env = System.getenv()

def adminStrategy(GlobalMatrixAuthorizationStrategy strategy, String groups) {
  String[] groupList = groups.split()
  for (String group : groupList) {
    // Roles based on https://wiki.jenkins-ci.org/display/JENKINS/Matrix-based+security
    //Overall - http://javadoc.jenkins-ci.org/jenkins/model/Jenkins.html
    strategy.add(Jenkins.ADMINISTER, group)
    strategy.add(Jenkins.RUN_SCRIPTS, group)
    strategy.add(Jenkins.READ, group)

    strategy.add(Jenkins.ADMINISTER, group)
    strategy.add(Jenkins.RUN_SCRIPTS, group)
    strategy.add(Jenkins.READ, group)

    // Agent (Slave < 2.0) - http://javadoc.jenkins-ci.org/jenkins/model/Jenkins.MasterComputer.html
    strategy.add(Jenkins.MasterComputer.BUILD, group)
    strategy.add(Jenkins.MasterComputer.CONFIGURE, group)
    strategy.add(Jenkins.MasterComputer.CONNECT, group)
    strategy.add(Jenkins.MasterComputer.CREATE, group)
    strategy.add(Jenkins.MasterComputer.DELETE, group)
    strategy.add(Jenkins.MasterComputer.DISCONNECT, group)

    // Job - http://javadoc.jenkins-ci.org/hudson/model/Item.html
    strategy.add(hudson.model.Item.BUILD, group)
    strategy.add(hudson.model.Item.CANCEL, group)
    strategy.add(hudson.model.Item.CONFIGURE, group)
    strategy.add(hudson.model.Item.CREATE, group)
    strategy.add(hudson.model.Item.DELETE, group)
    strategy.add(hudson.model.Item.DISCOVER, group)
    strategy.add(hudson.model.Item.EXTENDED_READ, group)
    strategy.add(hudson.model.Item.READ, group)
    strategy.add(hudson.model.Item.WIPEOUT, group)
    strategy.add(hudson.model.Item.WORKSPACE, group)

    // Run - http://javadoc.jenkins-ci.org/hudson/model/Run.html
    strategy.add(hudson.model.Run.DELETE, group)
    strategy.add(hudson.model.Run.UPDATE, group)
    strategy.add(hudson.model.Run.ARTIFACTS, group)

    // View - http://javadoc.jenkins-ci.org/hudson/model/View.html
    strategy.add(hudson.model.View.CONFIGURE, group)
    strategy.add(hudson.model.View.CREATE, group)
    strategy.add(hudson.model.View.DELETE, group)
    strategy.add(hudson.model.View.READ, group)

    // SCM - http://javadoc.jenkins-ci.org/hudson/model/View.html
    strategy.add(hudson.scm.SCM.TAG, group)

    // Plugin Manager http://javadoc.jenkins-ci.org/hudson/PluginManager.html
    strategy.add(hudson.PluginManager.UPLOAD_PLUGINS, group)
    strategy.add(hudson.PluginManager.CONFIGURE_UPDATECENTER, group)
  }

  return strategy
}

def readOnlyStrategy(GlobalMatrixAuthorizationStrategy strategy, String groups) {
  String[] groupList = groups.split()
  for (String group : groupList) {
    strategy.add(Jenkins.READ, group)
    strategy.add(hudson.model.Item.READ, group)
    strategy.add(hudson.model.View.READ, group)
    strategy.add(hudson.model.Item.READ, group)
  }
  return strategy
}

if (hudsonRealm.getAllUsers().size == 0){
	hudsonRealm.createAccount("admin", "admin")
	instance.setSecurityRealm(hudsonRealm)
	 
	def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
	strategy.setAllowAnonymousRead(false)
	instance.setAuthorizationStrategy(strategy)
	instance.save()
	 
	Jenkins.instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)
}

enableOpenId = env['OPENID_ENABLE']
if (enableOpenId.toLowerCase() == "true") {
  String clientId = env['OPENID_CLIENTID']
  String clientSecret = env['OPENID_CLIENT_SECRET']
  String tokenServerUrl = env['OPENID_TOKEN_SERVER_URL']
  String authorizationServerUrl = env['OPENID_AUTH_SERVER_URL']
  String userInfoServerUrl = ''
  String userNameField = 'email'
  String tokenFieldToCheckKey = ''
  String tokenFieldToCheckValue = ''
  String fullNameFieldName = 'name'
  String emailFieldName = 'email'
  String scopes = 'openid email profile groups'
  String groupsFieldName = 'groups'
  boolean disableSslVerification = 'false'
  boolean logoutFromOpenidProvider = 'false'
  String endSessionUrl = ''
  String postLogoutRedirectUrl = ''
  boolean escapeHatchEnabled = 'false'
  String escapeHatchUsername = ''
  String escapeHatchSecret = ''
  String escapeHatchGroup = ''

  adrealm = new OicSecurityRealm(
    clientId,
    clientSecret,
    tokenServerUrl,
    authorizationServerUrl,
    userInfoServerUrl,
    userNameField,
    tokenFieldToCheckKey,
    tokenFieldToCheckValue,
    fullNameFieldName,
    emailFieldName,
    scopes,
    groupsFieldName,
    disableSslVerification,
    logoutFromOpenidProvider,
    endSessionUrl,
    postLogoutRedirectUrl,
    escapeHatchEnabled,
    escapeHatchUsername,
    escapeHatchSecret,
    escapeHatchGroup
  )

  String adminGroups = env['OPENID_ADMIN_GROUPS']
  String readOnlyGroups = env['OPENID_READ_ONLY_GROUPS']
  def strategy = new GlobalMatrixAuthorizationStrategy()

  strategy = readOnlyStrategy(strategy, readOnlyGroups)
  strategy = adminStrategy(strategy, adminGroups)

  instance.setAuthorizationStrategy(strategy)
  instance.setSecurityRealm(adrealm)
  instance.save()
}


System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")
