terraform {
  backend "s3" {
    bucket = "legion-ci-configuration"
    key    = "terraform/state"
    region = "eu-central-1"
  }
}

variable "AWS_INSTANCE_TYPE" {}
variable "INSTANCE_NAME" {}
variable "AWS_REGION" {}
variable "AWS_SECURITY_GROUPS" {}
variable "AWS_IMAGE" {}
variable "AWS_KEY_NAME" {}
variable "AWS_SUBNET_ID" {}
variable "AWS_VOLUME_SIZE" {}

provider "aws" {
    region = "${var.AWS_REGION}"
}

resource "aws_instance" "legion-k8s-master" {

    root_block_device {
        volume_type = "standard"
        volume_size = "${var.AWS_VOLUME_SIZE}"
    }

    volume_tags {
        Name = "${var.INSTANCE_NAME}-volume"
    }

    ami = "${var.AWS_IMAGE}"
    instance_type = "${var.AWS_INSTANCE_TYPE}"

    tags {
        Name = "${var.INSTANCE_NAME}"
    }

    subnet_id = "${var.AWS_SUBNET_ID}"
    vpc_security_group_ids = ["${split(",", var.AWS_SECURITY_GROUPS)}"]
    associate_public_ip_address = true

    key_name = "${var.AWS_KEY_NAME}"
}


resource "aws_eip" "legion-k8s-master-ip" {
    vpc = true
    instance = "${aws_instance.legion-k8s-master.id}"
}

output "public_ip" {
  value = "${aws_eip.legion-k8s-master-ip.public_ip}"
}

output "private_ip" {
  value = "${aws_instance.legion-k8s-master.private_ip}"
}

