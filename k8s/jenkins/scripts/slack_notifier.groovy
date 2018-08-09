import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.*
import hudson.util.Secret
import java.nio.file.Files
import jenkins.model.Jenkins
import net.sf.json.JSONObject
import org.jenkinsci.plugins.plaincredentials.impl.*

// parameters
def slackCredentialParameters = [
  description:  'Slack Jenkins integration token',
  id:           'slack-token',
  secret:       "${jenkins.slack.token}"
]
 
def slackParameters = [
  slackBaseUrl:             "${jenkins.slack.slackBaseUrl}",
  slackBotUser:             'false',
  slackRoom:                '#dynmodels',
  slackTeamDomain:          "${jenkins.slack.slackTeamDomain}",
  slackToken:               '',
  slackTokenCredentialId:   'slack-token'
]
 
// get Jenkins instance
Jenkins jenkins = Jenkins.getInstance()
 
// get credentials domain
def domain = Domain.global()
 
// get credentials store
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
 
// get Slack plugin
def slack = jenkins.getExtensionList(jenkins.plugins.slack.SlackNotifier.DescriptorImpl.class)[0]
 
// define secret
def secretText = new StringCredentialsImpl(
  CredentialsScope.GLOBAL,
  slackCredentialParameters.id,
  slackCredentialParameters.description,
  Secret.fromString(slackCredentialParameters.secret)
)
 
// define form and request
JSONObject formData = ['slack': ['tokenCredentialId': 'slack-token']] as JSONObject
def request = [getParameter: { name -> slackParameters[name] }] as org.kohsuke.stapler.StaplerRequest
 
// add credential to Jenkins credentials store
store.addCredentials(domain, secretText)
 
// add Slack configuration to Jenkins
slack.configure(request, formData)
 
// save to disk
slack.save()
jenkins.save()