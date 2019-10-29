# Legion Model Artifact format

This format declares, how you can store ML models, built on different languages (Python, Java, etc) 
with wide range of machine-learning libs used (scikit-learn, tensorflow, keras, etc.).

Legion Model Artifact is representative as file-system folder packed to ZIP file using Deflate ZIP compression algorithm.

Legion Model Artifact folder contains of next objects:

* `legion.model.yaml` file in root folder - contains meta information about type of binary model and other model
related information (e.g. language, import endpoints, dependencies).

* Additional folders and files, depend on meta information declared in `legion.model.yaml`.


## Meta information file legion.model.yaml

This file, as previously stated, contains all information about model and additional folders and files.
This file is in YAML format.

Structure of file:

* `binaries` - section that declares what environment (language and dependencies mechanisms) should be used 
for loading this model binaries.
  
* `binaries.type` - name of supported Legion Model Environments. 
Please see section [Legion Model Environments](#legion-model-environments).

* `binaries.dependencies` - name of dependency management system, that is compatible 
with [Legion Model Environments](#legion-model-environments) chosen in `binaries.type`.

* `binaries.<additional>` - additional values for Model Environment, dependency management system 
(such as path to requirements file).

* `model` - section that describes where model artifacts is. Model artifact format depends on [Legion Model Environment](#legion-model-environments).

* `model.name` - name of model, `[a-Z0-9\-]+` string that does not start from digit.

* `model.version` - version of model. Format is `<Apache Version>-<Additional suffix>`, 
where `Additional suffix` is a `[a-Z0-9\-\.]+` string.

* `model.workDir` - working directory to start model from.

* `model.entrypoint` - name of model artifact (e.g. Python module or Java JAR file).

* `legionVersion` - version of Legion Model Artifact format.

* `toolchain` - section that describes toolchain used for training and preparing Legion Model Artifact.

* `toolchain.name` - name of used toolchain.

* `toolchain.version` - version of used toolchain.

* `toolchain.<additional>` - additional fields, related to used toolchain (e.g. used submodule of toolchain).

Examples:

Example with GPPI using conda for dependency management, mlflow toolchain.
```
binaries:
  type: python
  dependencies: conda
  conda_path: mlflow/model/mlflow_env.yml
model:
  name: wine-quality
  version: 1.0.0-12333122
  workDir: mlflow/model
  entrypoint: entrypoint
legionVersion: '1.0'
toolchain:
  name: mlflow
  version: 1.0.0
```

## Legion Model Environments

Nowadays, legion supports next kinds of model environments:

* General Python Prediction Interface (GPPI), that provides an ability to import trained model 
as a python module and use one of predefined function for predicting. Value for `binaries.type` is `python`.

* General Java Prediction Interface (GJPI), that provides an ability to import trained model
as a Java Library and use one of predefined interfaces for predicting. Value for `binaries.type` is `java`.

### Legion's General Python Prediction Interface (GPPI)

#### General information

| Field                 | Value                                      |
|-----------------------|--------------------------------------------|
| Name                  | General Python Prediction Interface (GPPI) |
| Supported languages   | Python 3.6+                                |
| binaries.type         | "python"                                   |
| binaries.dependencies | "conda"                                    |
| binaries.conda_path   | Path to conda env, from artifact root      |
| model.workDir         | Working directory, PYTHON PATH             |
| model.entrypoint      | Python import, relative to model.workDir   |

#### Description
This interface is representable as importable Python module with declared interface 
(functions with arguments and return types). 
Toolchains, that want to save models in this format, have to provide `entrypoint` with this interface 
as a python module, or, they may provide a wrapper around their interface for this interface.

#### ENV. variables required

* MODEL_LOCATION -- path to model's file, relative to working directory.

#### Interface declaration
Interface consists of next functions:

| Function                   | Description                                                                                                          |
|----------------------------|----------------------------------------------------------------------------------------------------------------------|
| init                       | Required. Is being invoked during service boot. Returns prediction mode: object-based or matrix-based.               |
| predict_on_objects         | Optional. Make prediction based on input objects. Return type is configurable.                                       |
| get_object_input_type      | Optional. Get type of input for `predict_on_objects`. List of dicts used if is not provided.                         |
| get_object_output_type     | Optional. Get output type of `predict_on_objects`. Otherwise they returns JSON-serializable list of dicts.           |
| predict_on_matrix          | Optional. Make prediction based on matrix with values (tuple of tuples). Accepts names of columns. Returns matrix.   |
| get_output_json_serializer | Optional. Is used for output serialization if declared. Default is used otherwise.                                   |
| get_info                   | Optional. Returns OpenAPI description of input and output types if it is possible.                                   |


 