#!groovy
 
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