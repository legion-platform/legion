.. _mod_dev_using_mlflow-section:

====================================================
MLFlow Toolchain Training Integration
====================================================

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Support", "official"
    "Language", "Python 3.6+"


Legion provides officially supported :term:`Toolchain Train Integration` with `MLflow <https://www.mlflow.org/>`_ - `Legion MLflow <https://github.com/legion-platform/legion-mlflow>`_.

Installation instructions are available on
`official GitHub page <https://github.com/legion-platform/legion-mlflow>`_.

This integration allows to train models, written in Python with usage of MLflow API,
and to convert them into :term:`General Python Prediction Interface`
(that is :term:`Trained Model Binary Format`).


.. warning::

    To use train models, written using these integration, please ensure, that appropriate :term:`Toolchain Train Integration`
    has been installed on a platform (for cloud usage).

    Installation instructions are available on `official GitHub page <https://github.com/legion-platform/legion-mlflow>`_.


Limitations
-----------

- Legion supports all model flavours, that have Python flavor (e.g. keras, sklearn and etc.). MLeap flavour is not supported;

- Only Python programming language version 3 is supported;

- MLproject has to use conda environment management, all required packages (python and system) has to be declared in conda environment file;

- Training code may save only one model in one MLproject entry point, otherwise exception will be raised;

- To allow using names of input / output columns, artifacts named ``head_input.pkl`` and ``head_output.pkl`` have to be saved in artifact's folder;

- Legion executes exact one entry point during :term:`Model Training process`;

- Direct usage of MLflow client inside model training code is undesirable;
