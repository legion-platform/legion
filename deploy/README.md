#

1)Before start terrafrom script please create ssh keys for user and add to folder
/deploy/keys/sshkey
/deploy/keys/sshkey.pub

2) Add AWS account keys to file /terraform/variable.tf
variable "access_key" {
        default = "#########"
}
variable "secret_key" {
        default = "#####################"
}
variable "region" {
    default = "eu-central-1"
}

