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

// File file = new File("/tmp/vault/${slack_s3_filename}")
// def decryptToken = file.getText()

// parameters
def slackCredentialParameters = [
  description:  'Slack Jenkins integration token',
  id:           'slack-token',
  secret:       "${decryptToken}"
]
 
def slackParameters = [
  slackBaseUrl:             "${jenkins.slack.slackBaseUrl}",
  slackBotUser:             'false',
  slackRoom:                '#ada_nbcustomer_algo',
  slackTeamDomain:          "${jenkins.slack.slackTeamDomain}",
  slackToken:               "${jenkins.slack.token}",
  slackTokenCredentialId:   'slack-token'
]
 
Jenkins jenkins = Jenkins.getInstance()
def domain = Domain.global()
def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
def slack = jenkins.getExtensionList(jenkins.plugins.slack.SlackNotifier.DescriptorImpl.class)[0]
 
def secretText = new StringCredentialsImpl(
  CredentialsScope.GLOBAL,
  slackCredentialParameters.id,
  slackCredentialParameters.description,
  Secret.fromString(slackCredentialParameters.secret)
)

JSONObject formData = ['slack': ['tokenCredentialId': 'slack-token']] as JSONObject
def request = [getParameter: { name -> slackParameters[name] }] as org.kohsuke.stapler.StaplerRequest

store.addCredentials(domain, secretText)
slack.configure(request, formData)

slack.save()
jenkins.save()