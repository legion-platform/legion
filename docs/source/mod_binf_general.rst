.. _mod_binf_general-section:

===========================
Trained Model Binary Format
===========================

Legion Platform declares formats, in which trained models have to be saved.
:term:`Model Packagers <Model Packager>` rely on these formats.
Each packager specifies which parameters does it support.

This format declares, how you can store ML models, built on different languages (Python, Java, etc)
with wide range of machine-learning libs used (scikit-learn, tensorflow, keras, etc.).

Trained Model Binary is representative as file-system folder packed to ZIP file using Deflate ZIP compression algorithm.
This folder contains of next objects:

- ``legion.model.yaml`` file in root folder - contains meta information about type of binary model and other model
  related information (e.g. language, import endpoints, dependencies).

- Additional folders and files, depend on meta information declared in ``legion.model.yaml``.


Meta information file legion.model.yaml
---------------------------------------

This file, as previously stated, contains all information about model and additional folders and files.
This file is in YAML format.

Structure of file:

- ``binaries`` - section that declares what environment (language and dependencies mechanisms) should be used
  for loading this model binaries.

- ``binaries.type`` - name of supported Legion Model Environments.

- ``binaries.dependencies`` - name of dependency management system, that is compatible
  with this format.

- ``binaries.<additional>`` - additional values for Model Environment, dependency management system
  (such as path to requirements file).

- ``model`` - section that describes where model artifacts is.

- ``model.name`` - name of model, ``[a-Z0-9\-]+`` string that does not start from digit.

- ``model.version`` - version of model. Format is ``<Apache Version>-<Additional suffix>``,
  where `Additional suffix` is a ``[a-Z0-9\-\.]+`` string.

- ``model.workDir`` - working directory to start model from.

- ``model.entrypoint`` - name of model artifact (e.g. Python module or Java JAR file).

- ``legionVersion`` - version of Legion Model Artifact format.

- ``toolchain`` - section that describes toolchain used for training and preparing Legion Model Artifact.

- ``toolchain.name`` - name of used toolchain.

- ``toolchain.version`` - version of used toolchain.

- ``toolchain.<additional>`` - additional fields, related to used toolchain (e.g. used submodule of toolchain).


Examples
~~~~~~~~~

Example with GPPI using conda for dependency management, mlflow toolchain.

.. code-block:: yaml

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


Supported formats
-----------------

- :ref:`mod_binf_gppi-section` - provides an ability to import trained model
  as a python module and use one of predefined function for predicting.
  Value for ``binaries.type`` is ``python``.

