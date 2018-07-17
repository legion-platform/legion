#!groovy
/**
 *   Copyright 2018 EPAM Systems
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
 
def instance = Jenkins.getInstance()
 
def hudsonRealm = new HudsonPrivateSecurityRealm(false)

if (hudsonRealm.getAllUsers().size == 0){
	hudsonRealm.createAccount("admin", "admin")
	instance.setSecurityRealm(hudsonRealm)
	 
	def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
	strategy.setAllowAnonymousRead(false)
	instance.setAuthorizationStrategy(strategy)
	instance.save()
	 
	Jenkins.instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)
}

System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")