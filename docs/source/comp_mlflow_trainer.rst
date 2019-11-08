.. _mod_dev_using_mlflow-section:

==============
MLFlow Trainer
==============

Legion provides a :term:`Trainer Extension` for the popular `MLflow <https://www.mlflow.org/>`_ framework.

This allows Python model :term:`Training <Train>` in Python, and provides support for MLflow APIs. Trained models are
packaged using the :term:`General Python Prediction Interface`.

Limitations
-----------

- Legion supports Python (v. 3) libraries (e.g. Keras, Sklearn, TensorFlow, etc.)
- MLeap is not supported
- Required packages (system and python) must be declared in a conda environment file
- Train may save only one model, using one MLproject entry point method. Otherwise an exception will occur
- Input and output columns must be mapped to the specially-named ``head_input.pkl`` and ``head_output.pkl`` files to make it into the Packaged artifact
- Training code should avoid direct usage of MLflow client libraries

Implementation Details
----------------------

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Support", "official"
    "Language", "Python 3.6+"

Source code is available on `GitHub <https://github.com/legion-platform/legion-mlflow>`_.

Low-level integration details are provided `here <https://github.com/legion-platform/legion-mlflow>`_.
