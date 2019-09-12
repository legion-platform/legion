# Legion's CRDs

Legion contains next CustomResourceDefinitions:
* [ModelTraining](#modeltraining) - for declaring model training (converting models from source code to images), requires [VCSCredential](#vcscredential) for source code credentials.
* [VCSCredential](#vcscredential) - for providing credentials for checking out source codes.
* [ModelDeployment](#modeldeployment) - for deploying model on cluster.

## ModelTraining
```yaml
toolchain: "python"  # Type of toolchain. Currently supports only python. Required.
image: ~  # Image for starting train srcipt. Optional (toolchain-depended will be used).
vcsName: "vcs-1"  # Name of VCSCredential resource. Required.
reference: "develop"  # Custom reference in source code repository (tag, sha1, branch). Default is used if this value is not provided. Optional.
entrypoint: "entry.py"  # File to start. Required.
args: []  # Arguments for starting entry point. List of strings. Optional.
env: {}  # Map of ENV variable name => ENV variable value. Will be provided to entry point file. Optional.
hyperparameters: {}  # Map with hyperparemeters's names and values. Optional.
modelFile: ~  # Name of model file to save in. (Temporarily storing path, optional). Optional.
```

## VCSCredential
```yaml
credential: ~  # Credentialss for VCS. Optional. In case of GIT should be base64-encoded private key.
defaultReference: ~  # Default reference in VCS, e.g. branch, commit, tag and etc.
publicKey: ~  # Public keys in base64 format for ssh know hosts. You can gather it using "ssh-keyscan". Optional
type: "git"  # Type of VCS. Currently supports only git.
uri: "git@github.com:legion-platform/legion.git"  # VCS uri. For Git valid format is: git@github.com:legion-platform/legion.git. Required
```

## ModelDeployment
TBD