# Configuring

## Configuring Legion HELM chart
```yaml
# Version of Legion
# By default .Chart.AppVersion version is used
# Type: string
# legionVersion: "1.0"

# Does cluster require RBAC
# Type: bool
rbac: true

# Docker images registry
# This registry will be used for automatic docker image name deduction based on Legion naming for images
# Each image could be overridden manually in .<service>.image, please see .edi root section or other
# Type: string
imagesRegistry: legionplatform/

# Verbosity of logging features in components
# Valid values are:
# - info
# - debug
# - warning
# - error
logLevel: info

# Configuration of Legion ingresses
# Ingresses are for next <service>s
# - edi
# - edge
ingress:
  # Global flag for Ingress enabling
  # Each Ingress could be configured manually in .<service>.ingress.enabled
  # Type: bool
  enabled: false

  # Root domain for auto-created Ingress domains.
  # Each domain could be configured manually in .<service>.ingress.domain
  # Also it controls building URLs for external resources such as auth endpoint
  # Type: string
  globalDomain: example.com

  # Global annotations for all services
  # Each Ingress could be configured manually in .<service>.ingress.annotations
  # Type: string->string map
  annotations: {}
  #  kubernetes.io/ingress.class: nginx
  #  kubernetes.io/tls-acme: "true"

  # Global TLS flag
  # Each Ingress could be configured manually in .<service>.ingress.tlsEnabled
  # Also it controls building URLs for external resources such as auth endpoint
  # Type: bool
  tlsEnabled: false

  # Global TLS secret name
  # Each Ingress could be configured manually in .<service>.ingress.tlsSecretName
  # Type: string
  tlsSecretName: ~

# Security configuration. Model API security configures in .modelApiSecurity section (see below)
security:
  # Is authorization for WEB requests enabled or not
  # Type: bool
  enabled: false

  # Type of authorization. Currently only oauth2_proxy is supported
  # Valid values are:
  # - oauth2_proxy
  integration: oauth2_proxy

  # Detail configuration of oauth2_proxy
  oauth2_proxy:
    # Internal URL of oauth2_proxy that will be called on each Ingress request. Is used in auth_request directive on Ingress Nginx
    # Type: string
    url: http://oauth2-proxy.kube-system.svc.cluster.local:4180/oauth2/auth

    # Public URL on which user will be redirected for authrorization
    # Uncomment for custom public URL, otherwise auth.<ingress.globalDomain> will be used
    # besides standard Nginx Ingress variables, escaped_request_uri is available too
    # Type: string
    # public_url: https://auth.my-company.com/oauth2/start?rd=https://$host$escaped_request_uri

# Model API security
modelApiSecurity:
  # Should Model API security be closed by auth. or not
  # Type: bool
  enabled: false

  # Type of auth. mechanism for Model API gateway
  # Valid values are:
  # - jwt
  integration: jwt

  # Detailed JWT configuration
  jwt:
    # Secret for JWT
    # Type: string
    secret: example

    # Default token's TTL in minutes
    # Type: integer
    defaultTokenTTLInMinutes: 120

    # Maximum value of TTL in minutes
    # This value is used in EDI to validate requests for token generation
    # Type: integer
    maxTokenTTLInMinutes: 525600

    # Default TTL end date
    # Type: date sting, e.g. 2030-12-30T00:00:00
    defaultTokenTTLEndDate: "2030-12-30T00:00:00"


# Components metrics measurement
# Measures components performance through prometheus protocol
metrics:
  # Is measurements enabled or not
  # Type: bool
  enabled: false

  # Labels for ServiceMonitor CR objects
  # Type: string -> string map
  serviceMonitoringLabels:
    monitoring: prometheus


# StatsD configuration for metrics that requires StatsD format (e.g. model invocation & training metrics)
modelMetrics:
  # Is model performance metrics enabled or not
  # Type: bool
  enabled: false

  # StatsD host
  # Type: string
  host: statsd-exporter.kube-monitoring.svc.cluster.local

  # StatsD port
  # Type: integer
  port: 9125


# Default VCS instances. Will be spawned on cluster start
# For more information, read the VCSCredential documentation. Example:
# - name: "legion"
#   type: "git"
#   uri: "git@github.com:legion-platform/legion.git"
#   defaultReference: "origin/develop"
#   creds: ""
vcs: []

# Model storage is a Docker Registry
# Credentials are required for gathering model information
modelStorage:
  # Prefix for all built images
  # Might be useful for management purposes
  # Type: string
  buildPrefix: "legion"

  # Type of Docker Registry.
  # Valid values are:
  # - external - use external Docker Registry
  type: external
  # TODO: add "internal" variant - deploy and use internal Docker Registry with ephemeral disk (only for development purposes)

  # Detailed configuration of external Docker Registry
  external:
    # Protocol for connection to Docker Registry
    # Valid values are:
    # - https
    # - http
    protocol: ~

    # URL of Docker Registry
    # Type: string
    url: ~

    # Credentials on Docker Registry
    # Type: string
    user: example

    # Credentials on Docker Registry
    # Type: string
    password: example


# Configuration of model execution process
modelExecution:
  # Limitations of model deployment pods
  # For declaration format see https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
  limits:
    cpu: 256m
    mem: 256Mi

# Feedback configuration
feedback:
  # Is feedback gathering stack enabled or not
  enabled: false

  fluentd:
    # This variable can be enabled to setup custom image name for fluentd
    # Type: string
    # image: custom-image:1.0

    # Resources for each instance
    # For declaration format see https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
    resources:
      requests:
        cpu: "300m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "1024Mi"

    # Input port number
    # Type: integer
    port: 24224

  output:
    # Where feedback data should be stored
    # Only S3 is supported nowadays
    # Valid values:
    # s3 - AWS S3
    target: s3

    # Detail configuration for storing on S3
    s3:
      # Type of authorization on S3
      # Valid values are:
      # - iam - requires kube2iam to be installed in cluster,
      #         adds annotation "iam.amazonaws.com/role" to FluentD Pod
      #         value of annotation could be specified in .feedback.output.s3.customIAMRole
      # - secret - provide AWS Key ID and AWS Secret Key in ENV variables for FluentD server
      #            AWS Key ID and AWS Secret Key should be specified in
      #            .feedback.output.s3.AWSKeyID and .feedback.output.s3.AWSSecretKey
      authorization: iam

      # Custom name for IAM for iam-based authorization mode of FluentD
      # For details see authorization directive above
      # By default "<.ingress.globalDomain>-<.Release.Namespace>-collector-role" is used
      # Type: string
      #customIAMRole: ~

      # AWS Key ID for secret-based authorization mode of FluentD
      # For details see authorization directive above
      # Type: string
      #AWSKeyID: ~

      # AWS Secret Key for secret-based authorization mode of FluentD
      # For details see authorization directive above
      # Type: string
      #AWSSecretKey: ~

      # S3 bucket name
      # Type: string
      bucket: ~

      # S3 region
      # Type: string
      region: ~

      # Directory for data storing
      # Type: string
      path: "model_log/${tag}/${model_id}/${model_version}/year=%Y/month=%m/day=%d/"

      # Format of file names
      # Type: string
      objectKeyFormat: "%{path}%{time_slice}_%{index}.%{file_extension}"

      # Slicing format
      # Type: string
      timeSliceFormat: "%Y%m%d%H"

      # Slicing wait time
      # Type: string
      timeSliceWait: "5m"

      # Storage type
      # Type: string
      storeAs: "json"

      # Storage format
      # Type: string
      format: "json"

      # Buffering (chunking)
      buffering:
        # Chunks length (window size)
        # Type: string
        timekey: 1m

        # Delay for flush (after end of window)
        # Type: string
        timekeyWait: 0s

        # Temporary buffering location
        # Type: string
        path: /tmp

# Operator configuration
# Operator handles all Legion's CustomResources such as ModelTraining and etc.
operator:
  # Operator's server configuration
  # It listens Kubernetes API for Legion CR update events
  #  and creates/updates appropriate Pods / Secrets
  server:
    # This variable can be uncommented to setup custom image name for operator (server)
    # Type: string
    # image: custom-image:1.0

    # Count of operator replicas
    # Type: integer
    replicas: 1

    # Resources for each instance
    # For declaration format see https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
    resources:
      limits:
        cpu: "256m"
        memory: "256Mi"
      requests:
        cpu: "128m"
        memory: "128Mi"

  # Builder's configuration
  # It places in sidecar container for training pod
  #  and it is in charge of communicating with host's Docker socket
  #  for training container capturing.
  builder:
    # This variable can be uncommented to setup custom image name for operator (builder)
    # Type: string
    # image: custom-image:1.0

# EDI server configuration
# It provides HTTP API for model training & model deployment management
#  also it creates JWT tokens for model invocation
edi:
  # EDI could be disabled
  # Type: bool
  enabled: true

  # This variable can be uncommented to setup custom image name for operator (server)
  # Type: string
  # image: custom-image:1.0

  # Count of EDI replicas
  # Type: integer
  replicas: 1

  # Maximum number of retries for K8S API calls
  # Type: integer
  k8sApiRetryNumberMaxLimit: 10

  # Delay between retries for K8S API calls
  # Type: integer
  k8sApiRetryDelaySec: 3

  # Port on which EDI listens income traffic
  # Type: integer
  port: 80

  # Resources for each instance
  # For declaration format see https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
  resources:
    requests:
      cpu: "50m"
      memory: "128Mi"
    limits:
      cpu: "100m"
      memory: "512Mi"

  # Configuration of ingress object
  ingress:
    # Custom enabling/disabling of Ingress resource for EDI
    # To use specific value, uncomment and replace ~ with target value
    # Type: bool
    # enabled: ~

    # Annotations for ingress
    # Will be added to global annotations (.ingress.annotations)
    # Type: string->string map
    annotations: {}

    # Custom domain name
    # By default domain name "edi.<..ingress.globalDomain>" is used
    # To use specific value, replace ~ with target value
    # Type: string
    # domain: ~

    # Is TLS enabled for this Ingress or not
    # By default global variable is used (.ingress.tlsEnabled)
    # To use specific value, replace ~ with target value
    # Type: string
    # tlsEnabled: false

    # Global TLS secret name
    # By default global variable is used (.ingress.tlsSecretName)
    # To use specific value, replace ~ with target value
    # Type: string
    # tlsSecretName: ~

# EDGE gateway
# It handles all income traffic for model invocation
#  and it does JWT validation of requests if it is enabled
edge:
  # EDGE gateway could be disabled
  # Type: bool
  enabled: true

  # This variable can be uncommented to setup custom image name for operator (server)
  # Type: string
  # image: custom-image:1.0

  # Count of EDGE replicas
  # Type: integer
  replicas: 1

  # Port on which EDI listens income traffic
  # Type: integer
  port: 80

  # Resources for each instance
  # For declaration format see https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
  resources:
    requests:
      cpu: "50m"
      memory: "128Mi"
    limits:
      cpu: "100m"
      memory: "512Mi"

  # Ingress object configuration
  ingress:
    # Custom enabling/disabling of Ingress resource for EDGE
    # To use specific value, uncomment and replace ~ with target value
    # Type: bool
    #enabled: ~

    # Annotations for ingress
    # Will be added to global annotations (.ingress.annotations)
    # Type: string->string map
    annotations: {}

    # Custom domain name
    # By default domain name "edge.<..ingress.globalDomain>" is used
    # To use specific value, uncomment and replace ~ with target value
    # Type: string
    #domain: ~

    # Is TLS enabled for this Ingress or not
    # By default global variable is used (.ingress.tlsEnabled)
    # To use specific value, uncomment and replace ~ with target value
    # Type: string
    #tlsEnabled: ~

    # Global TLS secret name
    # By default global variable is used (.ingress.tlsSecretName)
    # To use specific value, uncomment and replace ~ with target value
    # Type: string
    #tlsSecretName: ~

toolchains:
  python:
    # This variable can be uncommented to setup custom image name for python
    # Type: string
    # image: custom-image:1.0

```

## Configuring CI/CD

Each cluster that you want to deploy with our Jenkinsfiles and ansible playbooks should be configured using **profiles** and **secrets**. For application configuration you may use **CLI configuration interface** or **environment variables configuration**.

**Profile** describes main characteristicts of cluster, such as DNS names, machines shapes (RAM, CPU and etc.) and so on.

**Secret** describes private cluster information, such as credentials for internal and external systems, secret keys and so on.

**CLI configuration interface** is a way to change Legion applications appearance (logging level, auth tokens and etc.) but may control only part of Legion applications configuration.

**Environment variables configuration** allows fully control Legion applications configurations.

### Profile

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
pypi_repo: "https://nexus-local.cc.epm.kharlamov.biz/repository/pypi-hosted/simple" # repository for Python packages
docker_repo: "nexus-local.cc.epm.kharlamov.biz:443" # docker registry with builded images
namespace: default      # namespace of core deployment
deployment: legion      # name of deployment
examples_to_test:       # which Jenkins examples will be executed in tests
  - Test-Summation
  - Digit-Recognition
model_id_to_test: income  # id of model which will be tested in EDI tests
enclaves:  # list of enclaves which will be automatically deployed after Legion deploy
  - company-a
legion_data_s3_bucket: "{{ legion_data_bucket_prefix }}-{{ env_name }}-{{ enclave }}"                              # Airflow storage location at S3

# Dex
dex:
  enabled: false   # by default Dex is disabled in profiles (but enabled in secrets)

# Secrets
secrets_bucket: "legion-secrets"               # S3 bucket with secrets
secrets_file: "/tmp/{{ cluster_name }}-secrets"  # path for temporary storage
```

### Secrets
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
    username: example
    password: example
    database_name: db

external_access_sgs: # list of AWS SG that should be added on ELB
  - sg-00000000
allowed_wan_ips:  # list of whitelisted CIDRs
  - 1.2.3.4/32
jenkins_cc_sg: sg-00000000 # CC Jenkins Security Group to be whitelisted on cluster

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
    - email: example@example.com
      password: example
      hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W" # bcrypt hash of the string "password"
      username: example
      userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"
  groups:  # GitHub groups mapping
  - clusterrolebinding: cluster-admin
    group: legion-platform:admin
  - clusterrolebinding: view
    group: legion-platform:view
```