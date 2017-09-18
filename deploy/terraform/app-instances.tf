/* Setup our aws provider */
provider "aws" {
  access_key  = "${var.access_key}"
  secret_key  = "${var.secret_key}"
  region      = "${var.region}"
}
resource "aws_instance" "drun-dev" {
  ami           = "ami-1e339e71"
  instance_type = "t2.medium"
  vpc_security_group_ids = ["sg-f1deca9a"]
  ebs_block_device {
        device_name = "/dev/sda1"
        volume_size = 16
    }


  key_name = "${aws_key_pair.deployer.key_name}"
  connection {
    user = "ubuntu"
    private_key = "${file("${path.module}/keys/sshkey")}"
  }
provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y apt-transport-https ca-certificates",
      "sudo curl -fsSL get.docker.com -o get-docker.sh",
      "sudo sh get-docker.sh",
      "sudo usermod -aG docker ubuntu",	
      "sudo curl -L https://github.com/docker/compose/releases/download/1.16.0-rc1/docker-compose-`uname -s`-`uname -m` > docker-compose",
      "sudo chmod +x docker-compose",
      "sudo mv docker-compose /usr/local/bin/",
      "sudo apt-get update",
      "mkdir -p /tmp/pyserve/runtime-cycle",
      "cd /tmp/pyserve/runtime-cycle/",
#      "sudo docker build -t pyserver/drun",
#      "sudo docker-compose up -d",
    ]
  }

  provisioner "file" {
    source = "../pyserve"
    destination = "/tmp"
  }

  provisioner "file" {
    source = "../Dockerfile"
    destination = "/tmp/pyserve/Dockerfile"
  }
  provisioner "file" {
    source = "../docker-compose.yml"
    destination = "/tmp/pyserve/docker-compose.yml"

  }
provisioner "remote-exec" {
    inline = [
      "cd /tmp/pyserve/",
      "sudo docker build -t pyserver/test .",
      "sudo docker-compose up -d",
    ]
  }

  tags = { 
    Name = "drun-dev"
  }
}

