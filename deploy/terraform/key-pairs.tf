resource "aws_key_pair" "deployer" {
  key_name = "deployer"
  public_key = "${file("${path.module}/keys/sshkey.pub")}" 
}

