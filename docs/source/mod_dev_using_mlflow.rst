.. _mod_dev_using_mlflow-section:

====================================================
Model Development Using MLflow Toolchain Integration
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


Examples
--------

Wine quality example (full code can be found `in GitHub repository <https://github.com/legion-platform/legion-mlflow/tree/master/examples/wine-quality>`_).

MLproject
~~~~~~~~~

Nothing changes are not required inside MLproject file.

.. code-block:: yaml
    :caption: MLproject
    :name: MLproject example file

    name: wine-quality-example

    conda_env: conda.yaml

    entry_points:
        main:
            parameters:
                alpha: float
                l1_ratio: {type: float, default: 0.1}
            command: "python train.py --alpha {alpha} --l1-ratio {l1_ratio}"

.. warn::

    Please remember, that you have to use conda_env (with conda.yaml file placed nearby),
    and you may use only one entry point during :term:`Model Training process`
    (you are free to declare multiple entry points in these file).


Conda environment file
~~~~~~~~~~~~~~~~~~~~~~

You can use any conda packages inside your conda env. file.

.. code-block:: yaml
   :caption: conda.yaml
   :name: Example conda env. file

    name: example
    channels:
    - defaults
    dependencies:
    - python=3.6
    - numpy=1.14.3
    - pandas=0.22.0
    - scikit-learn=0.19.1
    - pip:
        - mlflow==1.0.0
        - cloudpickle
        - azure-storage==0.36.0


Model training script
~~~~~~~~~~~~~~~~~~~~~

As said before, you are free to use MLflow's API methods. Example below demonstrates this.

.. code-block:: python
   :caption: train.py
   :name: Train script
   :linenos:
   :emphasize-lines: 46,48,59-64,66,69-72

    import os
    import warnings
    import sys
    import argparse

    import pandas as pd
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import ElasticNet

    import mlflow
    import mlflow.sklearn


    def eval_metrics(actual, pred):
        rmse = np.sqrt(mean_squared_error(actual, pred))
        mae = mean_absolute_error(actual, pred)
        r2 = r2_score(actual, pred)
        return rmse, mae, r2



    if __name__ == "__main__":
        warnings.filterwarnings("ignore")
        np.random.seed(40)

        parser = argparse.ArgumentParser()
        parser.add_argument('--alpha')
        parser.add_argument('--l1-ratio')
        args = parser.parse_args()

        # Read the wine-quality csv file (make sure you're running this from the root of MLflow!)
        wine_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wine-quality.csv")
        data = pd.read_csv(wine_path)

        # Split the data into training and test sets. (0.75, 0.25) split.
        train, test = train_test_split(data)

        # The predicted column is "quality" which is a scalar from [3, 9]
        train_x = train.drop(["quality"], axis=1)
        test_x = test.drop(["quality"], axis=1)
        train_y = train[["quality"]]
        test_y = test[["quality"]]

        alpha = float(args.alpha)
        l1_ratio = float(args.l1_ratio)

        with mlflow.start_run():
            lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
            lr.fit(train_x, train_y)

            predicted_qualities = lr.predict(test_x)

            (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

            print("Elasticnet model (alpha=%f, l1_ratio=%f):" % (alpha, l1_ratio))
            print("  RMSE: %s" % rmse)
            print("  MAE: %s" % mae)
            print("  R2: %s" % r2)

            mlflow.log_param("alpha", alpha)
            mlflow.log_param("l1_ratio", l1_ratio)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("mae", mae)
            mlflow.set_tag("test", '13')

            mlflow.sklearn.log_model(lr, "model")

            # Persist samples (input and output)
            train_x.head().to_pickle('head_input.pkl')
            mlflow.log_artifact('head_input.pkl', 'model')
            train_y.head().to_pickle('head_output.pkl')
            mlflow.log_artifact('head_output.pkl', 'model')


In this example, we're:

- Starting run context on line 46
- Training ``ElasticNet`` model on line 48
- Setting metrics, parameters and tags on lines 59-64
- Saving (through serialization) model with name ``model`` on line 66
- Saving input abd output samples (for persisting information about input and output column names) on lines 69-72


Managing MLflow trainings from Legion
-------------------------------------

To manage training of models with MLflow toolchain, you have to use next mapping:

- Working directory parameter should point at direcotry with file;
- Legion training's hypterparameters maps to MLflow run parameters, declared in MLproject file (``alpha`` and ``l1_ratio`` in case above);
- Legion toolchain's name should be set to mlflow;
- Legion training's entrypoint maps to ``entry_points``, declared in MLproject file;
