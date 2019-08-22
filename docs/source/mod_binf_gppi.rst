.. _mod_binf_gppi-section:

==========================================
General Python Prediction Interface (GPPI)
==========================================

.. csv-table::
   :stub-columns: 1
   :width: 100%

   "Name", "General Python Prediction Interface (GPPI)"
   "Supported languages", "Python 3.6+"
   "Support", "official"
   ``binaries.type``, ``python``
   ``binaries.dependencies``, ``conda``
   ``binaries.conda_path``, "Path to conda env, from artifact root"
   ``model.workDir``, "Working directory, PYTHON PATH"
   ``model.entrypoint``, "Python import, relative to ``model.workDir``"


This interface is representable as importable Python module with declared interface
(functions with arguments and return types).

Toolchains, that want to save models in this format, have to provide `entrypoint` with this interface
as a python module, or, they may provide a wrapper around their interface for this interface.


ENV. variables required
-----------------------

- ``MODEL_LOCATION`` -- path to model's file, relative to working directory.

Interface declaration
---------------------

.. csv-table::
   :header-rows: 1
   :stub-columns: 1
   :width: 100%

   Function, Description
   init, "Required. Is being invoked during service boot. Returns prediction mode: object-based or matrix-based."
   predict_on_objects, "Optional. Make prediction based on input objects. Return type is configurable."
   get_object_input_type, "Optional. Get type of input for `predict_on_objects`. List of dicts used if is not provided."
   get_object_output_type, "Optional. Get output type of `predict_on_objects`. Otherwise they returns JSON-serializable list of dicts."
   predict_on_matrix, "Optional. Make prediction based on matrix with values (tuple of tuples). Accepts names of columns. Returns matrix."
   get_output_json_serializer, "Optional. Is used for output serialization if declared. Default is used otherwise."
   get_info, "Optional. Returns OpenAPI description of input and output types if it is possible."

Example
-------

.. todo::

   Add example of manual creation