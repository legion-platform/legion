# Model Format

The **Legion Model Artifact Format** (LMAF) describes a format to package, store, and transport ML models.
 
Models can be built in different languages and use different platform libraries. For example: {Python, Scala, R, ...} 
using {scikit-learn, tensorflow, keras, ...}.

An LMAF **Artifact** is stored as a file-system folder packed into a ZIP file using the Deflate ZIP compression algorithm. 

The Artifact contains:

* `legion.model.yaml` a YAML file in the root folder. This file contains meta-information about the type of binary model 
and other model related information (e.g. language, import endpoints, dependencies).

* Additional folders and files, depending upon meta-information declared in `legion.model.yaml`.

## legion.model.yaml

File structure:

* `binaries` - Language and dependencies that should be used to load model binaries
* `binaries.type` - Required Legion Model Environments. See section [Legion Model Environments](#legion-model-environments).
* `binaries.dependencies` - Dependency management system, compatible with the selected Legion Model Environment 
* `binaries.<additional>` - Model Environment and dependency management system values, for example 'a path to the requirements file'
* `model` - Location of the model artifact Model artifact format depends on [Legion Model Environment](#legion-model-environments).
* `model.name` - name of the model, `[a-Z0-9\-]+`
* `model.version` - version of model. Format is `<Apache Version>-<Additional suffix>`, where `Additional suffix` is a `[a-Z0-9\-\.]+` string.
* `model.workDir` - working directory to start model from.
* `model.entrypoint` - name of model artifact (e.g. Python module or Java JAR file).
* `legionVersion` - LMAF version
* `toolchain` - toolchain used for training and preparing the Artifact
* `toolchain.name` - name of the toolchain
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

Legion supports these model environments:

* General Python Prediction Interface (GPPI). Can import a trained model as a python module and use a predefined function for prediction. Value for `binaries.type` should be `python`.

* General Java Prediction Interface (GJPI). Can import a trained model as a Java Library and use a predefined interfaces for prediction. Value for `binaries.type` should be `java`.

### Legion's General Python Prediction Interface (GPPI)

#### General Information

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

This interface is an importable Python module with a declared interface (functions with arguments and return types). Toolchains that save models in this format must provide an `entrypoint` with this interface or they may provide a wrapper around their interface for this interface.

#### Required Environment variables

* MODEL_LOCATION -- path to model's file, relative to working directory.

#### Interface declaration

Interface functions:

| Function                   | Description                                                                                                          |
|----------------------------|----------------------------------------------------------------------------------------------------------------------|
| init                       | Required. Invoked during service boot. Returns prediction mode: object-based or matrix-based.                        |
| predict_on_objects         | Optional. Make prediction based on input objects. Return type is configurable.                                       |
| get_object_input_type      | Optional. Get type of input for `predict_on_objects`. Defaults to List of Dicts if a value is not provided.          |
| get_object_output_type     | Optional. Get the output type of `predict_on_objects`. Otherwise it returns a JSON-serializable List of Dicts.       |
| predict_on_matrix          | Optional. Make prediction based on a value matrix (tuple of tuples). Accepts names of columns. Returns matrix.       |
| get_output_json_serializer | Optional. Serialize output, if declared. Otherwise, use default.                                                     |
| get_info                   | Optional. Return OpenAPI description of input and output types (if possible).                                        |
 