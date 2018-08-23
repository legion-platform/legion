# Configuring

Each cluster that you want to deploy with our Jenkinsfiles and ansible playbooks should be configured using **profiles** and **secrets**.

**Profile** describes main characteristicts of cluster, such as DNS names, machines shapes (RAM, CPU and etc.) and so on.

**Secret** describes private cluster information, such as credentials for internal and external systems, secret keys and so on.

## Profile

Each profile should be located in `/deploy/profiles` directory of current repository. Profile file name consists of two parts: envinroment name (usually equal to DNS name) and `.yml` extension.

File should consists of appropriate YAML formatted text.

### Profile format
Here is an example of profile file

```yaml
# DNS
base_domain: legion-dev.epm.kharlamov.biz     # DNS name of environment
route53_zone: epm.kharlamov.biz               # AWS Route53 zone on which domain will be created (zone should be parked before deploy)


# Common
vendor: legion          # name of vendor, will be used in resource tags
env_type: dev           # name of env. type, will be added in resource tags
env_name: legion-dev    # short name of env, will be added in resource tags


# Ansible variables
tmp_dir: /tmp/                          # directory for storing temporary files (on host during deploy)
git_key: "/home/jenkins/deploy.cert"    # SSH Git access key which will be copied to Jenkins in cluster 
ssh_public_key: ~/.ssh/id_rsa.pub       # public key which will be copied to cluster


# AWS configuration
aws_region: us-east-2      # target AWS region for EC2 instances
bastion_shape: t2.micro    # shape for bastion nodes (not as part of Kubernetes cluster)
master_shape: t2.large     # shape for masters
node_shape: t2.large       # shape for modes
node_autoscaler_min: 3     # minimum count of nodes for autoscaler group
node_autoscaler_max: 5     # maximum count of nodes for autoscaler group
node_extra_shapes:         # list of shapes that can be started up during model building of Jenkins (will be shutted down automatically)
  - r4.large       # 2 cpu   / 15.25Gb / $0.133 ph
  - r4.xlarge      # 4 cpu   / 30.5Gb  / $0.266 ph
  - r4.2xlarge     # 8 cpu   / 61Gb    / $0.532 ph
  - r4.4xlarge     # 16 cpu  / 122Gb   / $1.064 ph
  - r4.8xlarge     # 32 cpu  / 244Gb   / $2.128 ph
  - r4.16xlarge    # 64 cpu  / 488Gb   / $4.256 ph
  - x1.16xlarge    # 64 cpu  / 976Gb   / $6.669 ph
  - x1.32xlarge    # 128 cpu / 1952Gb  / $13.338 ph
node_extra_min: 0          # minimum count of nodes for model building
node_extra_max: 2          # maximum count of nodes for model building

vpc_id: vpc-5729c13e               # VPC id where the cluster will be created 


# Common cluster configuration for KOPS
cluster_name: legion-dev.epm.kharlamov.biz # unique KOPS cluster name
state_store: s3://legion-cluster  # AWS S3 bucket for storing KOPS state
aws_image: kope.io/k8s-1.8-debian-jessie-amd64-hvm-ebs-2018-02-08  # base Kubernetes image
kubernetes_version: 1.9.3         # kubernetes version
private_network: '172.31'         # private network prefix
cluster_zones:                    # configuration of cluster zones
  - zone_name: us-east-2a
    kops_cidr: "{{ private_network }}.100.0/24"
    kops_utility_cidr: "{{ private_network }}.103.0/24"
  - zone_name: us-east-2b
    kops_cidr: "{{ private_network }}.101.0/24"
    kops_utility_cidr: "{{ private_network }}.104.0/24"
  - zone_name: us-east-2c
    kops_cidr: "{{ private_network }}.102.0/24"
    kops_utility_cidr: "{{ private_network }}.105.0/24"


# TLS sertificates issuing configuration (via Let's Encrypt)
certificate_email: legion@epam.com      # Let's Encrypt notification email
cert_dir: "/etc/dynssl"                 # folder for storing SSL certificates on host

# Deploying and test configuration
use_https: "yes" # [?]
use_https_for_tests: "yes" # [?]
nexus_pypi_repo: "https://nexus-local.cc.epm.kharlamov.biz/repository/pypi-hosted/simple" # repository for Python packages
nexus_docker_repo: "nexus-local.cc.epm.kharlamov.biz:443" # docker registry with builded images
namespace: default      # namespace of core deployment
deployment: legion      # name of deployment
examples_to_test:       # which Jenkins examples will be executed in tests
  - Test-Summation
  - Digit-Recognition
model_id_to_test: income  # id of model which will be tested in EDI tests
enclaves:  # list of enclaves which will be automatically deployed after Legion deploy
  - company-a

# Airflow specific configuration
airflow_dags_dir: '/airflow-dags'                                        # Name of Aitflow DAGs directory
airflow_dags_pvc: legion-airflow-dags                                    # Name of Airflow DAGs PVC which will be created in Cluster
airflow_pvc: 200m                                                        # Airflow PVC size (for storing DAGs code)

# Airflow RDS configuration
airflow_rds_shape: "db.t2.medium"                                        # shape for Airflow RDS
airflow_rds_size: "50"                                                   # size of Airflow RDS in GB

# Airflow DAGs configuration [?]
airflow_s3_bucket_name: "epm-legion-data-{{ env_type }}-{{ enclave }}"                              # Airflow storage location at S3             
airflow_expected_output: 'expected-data/'                                # Configuration for Airflow DAGs

# Addons configuration
storageclass: efs              # Which storage use in PVCs
dashboard:                     # Kubernetes dashboard configuration
  version: "1.8.3"             # Dashboard version
  insecure: true               # Allow insecure access

# Dex
dex:
  enabled: false   # by default Dex is disabled in profiles (but enabled in secrets)

# Secrets
secrets_bucket: "legion-secrets"               # S3 bucket with secrets
secrets_file: "/tmp/{{ cluster_name }}-secrets"  # path for temporary storage
```

## Secrets 
Each secret should be encrypted with Ansible vault and uploaded to S3. 
Secret should be stored on a Jenkins like credentials file (for example vault-legion-dev.epm.kharlamov.biz).
S3 path to secrets builds using next template `{{ secrets_bucket }}/vault/{{ profile }}` for example `legion-secrets/vault/legion-dev.epm.kharlamov.biz`

Decrypted file should consists of appropriate YAML formatted text.

### Secrets format
Here is an example of secret file

```yaml
# AWS resources configuration
aws:
  account_id: 000000000000
  rds: # credentials for dynamically deployed RDS
    username: user
    password: pass
    database_name: db

# Airflow configuration
airflow:
  connections:  # list of airflow connections that will be automatically added during deploy
  # Connection to Aurora
  - connection_id: aurora_conn
    connection_type: mysql
    host: hostnamehere
    port: 3306
    login: readonly
    password: passwordhere

  # Connection to S3
  - connection_id: s3_conn
    connection_type: S3
    extra: {"bucket_prefix": "epm-legion-data"}
  
  # SMTP credentials for email notifications
  email:
    smtp_host: smtp.post.domain
    smtp_starttls: true
    smtp_ssl: true
    smtp_user: user
    smtp_port: 465
    smtp_password: password
    smtp_mail_from: mine.email@post.domain

  # Fernet key
  fernet_key: exampleexampleexample=

  # Airflow-slack integration
  slack:
    channel: airflow
    username: Airflow
    token: ""
  webserver:
    email_backend: "etl.slack.send_notification" # set email_backend to empty for Slack disabling notifications

# Fluentd configuration for event log collection
fluentd:
  aws: # Credentials for storing data on S3
    secret_access_key: AWS_SEC_KEY
    access_key_id: AWS_KEY_ID

external_access_sgs: # list of AWS SG that should be added on ELB
  - sg-00000000
allowed_wan_ips:  # list of whitelisted CIDRs
  - 20.10.30.40/32
jenkins_cc_sg: sg-00000000 # CC Jenkins Security Group to be whitelisted on cluster


# Airflow auth configuration
airflow_auth:
  enabled: true
  dex_group_admin: legion-platform:admin      # link to GitHub group
  dex_group_profiler: legion-platform:view    # link to GitHub group
  auth_backend: legion_airflow.auth.dex_auth  # Python auth backend

# DEX configuration
dex:
  enabled: true
  config:
    client_id: legion-dev.epm.kharlamov.biz # env. name ()
    client_secret: AAAAAAAAAAAAAAAA # randomly generated 24-len password
    connectors:
    - type: github
      id: github
      name: GitHub
      config:
        clientID: client_id
        clientSecret: client_secret
        redirectURI: https://dex.legion-dev.epm.kharlamov.biz/callback # DEX callback URL
        orgs:
        - name: legion-platform  # linked GitHub organizations
    staticPasswords:  # static hardcoded passwords for test
    - email: "user@example.com"      
      password: password
      hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W" # bcrypt hash of the string "password"
      username: "user"
      userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"
  groups:  # GitHub groups mapping
  - clusterrolebinding: cluster-admin
    group: legion-platform:admin
  - clusterrolebinding: view
    group: legion-platform:view
```