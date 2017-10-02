#!groovy
 
import jenkins.model.*
import hudson.plugins.git.*
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import hudson.triggers.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import hudson.plugins.sshslaves.*

// Create credentials
domain = Domain.global()
store = Jenkins.instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

if (store.getCredentials(domain).size() == 0){
	privateKey = new BasicSSHUserPrivateKey(
		CredentialsScope.GLOBAL,
		"drun-root-key",
		"git",
		new BasicSSHUserPrivateKey.UsersPrivateKeySource(),
		"",
		""
	);

	store.addCredentials(domain, privateKey);
}

// Create job

name = "DRUN-examples";
path = "jenkins/Jenkinsfile";
git = "git@github.com:akharlamov/drun-root.git";
triggerSchedule = "H/15 * * * *";

if (Jenkins.instance.getJobNames().size() == 0){
	userRemoteConfigs = [new UserRemoteConfig(git, null, null, "drun-root-key")];
	branches = [new BranchSpec("*/master")];
	scm = new GitSCM(userRemoteConfigs, 
		branches, 
		false, 
		[],
		null, null, 
		[]);

	trigger = new SCMTrigger(triggerSchedule);

	job = new WorkflowJob(Jenkins.instance, name);
	job.definition = new CpsScmFlowDefinition(scm, path);
	job.addTrigger(trigger)

	Jenkins.instance.add(job, name);
}