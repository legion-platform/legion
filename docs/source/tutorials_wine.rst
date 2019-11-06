
====================
MLFlow Wine quality
====================

In this tutorial you step by step will learn how to train, pack and deploy your model from scratch by using Legion Platform.

.. _tutorials_wine-req:

~~~~~~~~~~~~~~~~~~~
Requirements
~~~~~~~~~~~~~~~~~~~

- You must have the Legion Platform deployed in a cluster;
- :ref:`MLFlow <mod_dev_using_mlflow-section>` and :term:`docker <Docker REST API Packaging Toolchain Integration>` toolchain integrations must be installed;
- :term:`Legion CLI` is installed locally or :term:`Plugin for JupyterLab` is installed locally or in the cloud;
- You should be authorized at :ref:`edi-server-description`;

~~~~~~~~~~~~~~~~~~~
Tutorial
~~~~~~~~~~~~~~~~~~~

To train, pack and deploy model you need to interact with :ref:`edi-server-description` server.
This server provides REST API. You can use it directly or using different tools.

You have two options for such tools to complete this tutorial:

1. With using :term:`Legion CLI` command-line tool;
2. With using :term:`Plugin for JupyterLab`;

In this tutorial, you will learn how-to:

1. :ref:`Create MLFlow project <tutorials_wine-create-project>`;
2. :ref:`Manage connections for the project <tutorials_wine-manage-connections>`;
3. :ref:`Train a model of the project <tutorials_wine-train>`;
4. :ref:`Pack the trained model <tutorials_wine-pack>`;
5. :ref:`Deploy the packed model <tutorials_wine-deploy>`;
6. :ref:`Use the deployed model <tutorials_wine-use>`;

This tutorial uses a dataset to predict the quality of the wine based on quantitative features
like the wine’s "fixed acidity", "pH", "residual sugar", and so on.
The dataset is from `UCI’s machine learning repository <https://archive.ics.uci.edu/ml/datasets/Wine+Quality>`_.

The final code can be found at `GitHub <https://github.com/legion-platform/legion-examples/tree/master/mlflow/sklearn/wine>`_.



.. _tutorials_wine-create-project:

#########################
Create MLFlow project
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data", System with completed :ref:`requirements<tutorials_wine-req>`
    "Step output data", "Folder with MLFlow project to predict wine quality"

Create a new project folder:

.. code-block:: console

   $ mkdir wine && cd wine

Create our training script:

.. code-block:: console

   $ touch train.py

Paste next code to the created file:

.. code-block:: python
   :name: Train script
   :caption: train.py
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

In this file, we do:

- Starting run context on line 46;
- Training ``ElasticNet`` model on line 48;
- Setting metrics, parameters and tags on lines 59-64;
- Saving (through serialization) model with name ``model`` on line 66;
- Saving input and output samples (for persisting information about input and output column names) on lines 69-72;


Create MLproject file:

.. code-block:: console

   $ touch MLproject

Paste next code to the created file:

.. code-block:: yaml
    :caption: MLproject
    :name: MLproject file

    name: wine-quality-example
    conda_env: conda.yaml
    entry_points:
        main:
            parameters:
                alpha: float
                l1_ratio: {type: float, default: 0.1}
            command: "python train.py --alpha {alpha} --l1-ratio {l1_ratio}"

.. note::

    *Read more about MLproject structure at* `Official MLFlow docs <https://www.mlflow.org/docs/latest/projects.html>`_.


Create conda environment file:

.. code-block:: console

   $ touch conda.yaml

Paste next code to the created file:

.. code-block:: yaml
   :caption: conda.yaml
   :name: Conda environment for current project

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

.. note::

    All packages that tools that are used in training script must be listed at conda.yaml file.

    *Read more about conda environment at* `Official conda docs <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_.

Download wine data set:

.. code-block:: console

   $ mkdir ./data
   $ wget https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv -O ./data/wine-quality.csv

After this step project folder structure should look next way:

.. code-block:: text

    .
    ├── MLproject
    ├── conda.yaml
    ├── data
    │   └── wine-quality.csv
    └── train.py


.. _tutorials_wine-manage-connections:

###################################
Manage connections
###################################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data", "System with completed :ref:`requirements<tutorials_wine-req>`"
    "Step output data", "Created :term:`connections<Connection>`"


As mentioned before Legion Platform uses concept of :term:`Connections<Connection>`
to manage different kinds of data and other external services.

To complete this tutorial we will need next connections:

- :term:`Connection` to VCS repository where MLFlow project for wine classification is located
- :term:`Connection` to wine-quality.csv file in one of supported object storage
- :term:`Connection` to docker registry where the packed model will be stored


Create :term:`Connection` to VCS repository
---------------------------------------------

Because `legion-examples <https://github.com/legion-platform/legion-examples>`_ repository already contains the required code
we will just use this repository. But feel free to create and use a new repository if you want.

Create a directory where we will create all payloads for the Legion Platform API calls:

.. code-block:: console

    $ mkdir ./legion

Create payload:

.. code-block:: console

    $ touch ./legion/vcs_connection.legion.yaml

Paste next code to the created file:

.. code-block:: yaml
   :caption: vcs_connection.legion.yaml
   :name: VCS Connection

    kind: Connection
    id: legion-examples
    spec:
      type: git
      uri: git@github.com:legion-platform/legion-examples.git
      reference: origin/master
      keySecret: <paste here your key github ssh key>
      description: Git repository with legion-examples
      webUILink: https://github.com/legion-platform/legion-examples

.. note::

   Read more about `GitHub ssh keys <https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh>`_

Create connection using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/vcs_connection.legion.yaml

Or create a connection using :term:`Plugin for JupyterLab`:

1. Open jupyterlab (available by jupyterlab.<your-cluster-base-address>);
2. Open cloned repo, and then the folder with the project;
3. Select file ``./legion/vcs_connection.legion.yaml`` and in context menu press ``submit`` button;


Create :term:`Connection` to wine-quality.csv object storage
-------------------------------------------------------------

Create payload:

.. code-block:: console

    $ touch ./legion/wine_connection.legion.yaml

Paste next code to the created file:

.. code-block:: yaml
   :caption: wine_connection.legion.yaml
   :name: Wine connection

    kind: Connection
    id: wine
    spec:
      type: gcs
      uri: gs://<paste your bucket address here>/data/wine-quality.csv
      region: <paste region here>
      keySecret: <paste key secret here>
      description: Wine dataset

Create a connection using :term:`Legion CLI` or :term:`Plugin for JupyterLab` as in the previous example.

If wine-quality.csv is not persisted in store yet, you can copy it using:

.. code-block:: console

    $ gsutil cp ./data/wine-quality.csv gs://<bucket-name>/data/


Create :term:`Connection` to docker registry
---------------------------------------------

Create payload:

.. code-block:: console

    $ touch ./legion/docker_connection.legion.yaml

Paste next code to the created file:

.. code-block:: yaml
   :caption: docker_connection.legion.yaml
   :name: Docker connection

    kind: Connection  # type of payload
    id: docker-ci
    spec:
      type: docker
      uri: <past uri of your registry here>  # uri to docker image registry
      username: <paste your username here>
      password: <paste your password here>
      description: Docker registry for model packaging


Create the connection using :term:`Legion CLI` or :term:`Plugin for JupyterLab` as in the previous example.

Check all created connections:

.. code-block:: console

    $ legionctl conn get | grep -e id: -e type: -e description

    - id: docker-ci
        description: Docker repository for model packaging
        type: docker
    - id: legion-examples
        description: Git repository with legion-examples
        type: git
    - id: models-output
        description: Storage for trainined artifacts
        type: gcs
    - id: wine
        description: Wine dataset
        type: gcs

Congrats! Now you are ready to train your model!



.. _tutorials_wine-train:

##############################
Train a model of the project
##############################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data", "Folder with MLFlow project to predict wine quality"
    "Step output data", "The trained model in :term:`GPPI<General Python Prediction Interface>` :term:`Trained Model Binary Format`"

Create payload:

.. code-block:: console

    $ touch ./legion/training.legion.yaml

Paste next code to the created file:

.. code-block:: yaml
   :caption: ./legion/training.legion.yaml
   :name: ModelTraining
   :linenos:
   :emphasize-lines: 7-14,22

    kind: ModelTraining
    id: wine
    spec:
      model:
        name: wine
        version: 1.0
      toolchain: mlflow  # MLFlow training toolchain integration
      entrypoint: main
      workDir: mlflow/sklearn/wine  # directory where MLproject file is located
      data:
        - connName: wine
          localPath: mlflow/sklearn/wine/wine-quality.csv # where wine-quality.csv file from GCS should be fetched
      hyperParameters:
        alpha: "1.0"
      resources:
        limits:
          cpu: 4024m
          memory: 4024Mi
        requests:
          cpu: 2024m
          memory: 2024Mi
      vcsName: legion-examples

In this file, we do:

- line 7: legion toolchain's name should be set to :ref:`mlflow <mod_dev_using_mlflow-section>`;
- line 8: legion training's entry point maps to ``entry_points``, declared in :ref:`MLproject file`. We use ``main``;
- line 9: ``workDir`` point to MLFlow project directory (It is the directory that has :ref:`MLproject file` at the root level);
- line 10 section that describes where Legion Platform should take data and where this data should be downloaded;
- line 11: ``connName`` points to the id of :ref:`Wine connection` that we created before;
- line 12: ``localPath`` points to the path where the file with wine data should be downloaded;
- lines 13-14: training's hyperparameters maps to MLflow run parameters. ``l1_ratio`` will be set to a default value;
- line 22: ``vcsName`` should be equal to ``id`` of :ref:`VCS Connection`;


Create :term:`Model Training` using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/training.legion.yaml

Check :term:`Model Training` logs:

.. code-block:: console

    $ legionctl training logs --id wine

After some time :term:`Model Training` will be finished.

To check status run:

.. code-block:: console

    $ legionctl training get --id wine

You will see YAML with an updated ModelTraining resource. Look at the status section. You can see:

- ``state`` succeeded (this means that model training process was successful)
- ``artifactName`` (this is the filename of :term:`Trained Model Binary`)


Or create training using :term:`Plugin for JupyterLab`:

1. Open jupyterlab;
2. Open cloned repo, and then the folder with the project;
3. Select file ``./legion/training.legion.yaml`` and in context menu press ``submit`` button;

You can see model logs using ``Legion cloud mode`` left side tab (cloud icon) in your Jupyterlab:

1. Open ``Legion cloud mode`` tab;
2. Look for ``TRAINING`` section;
3. Press on the row with `ID=wine`;
4. Press button ``LOGS`` to connect to :term:`Model Training` logs;

After some time :term:`Model Training` will be finished. Status of training is updated in column ``status`` of the `TRAINING` section
in the ``Legion cloud mode`` tab. If model training finished with success you will see `status=succeeded`.

Then open :term:`Model Training` again by pressing the appropriate row. Look at the `Results` section. You can see:

- ``artifactName`` (this is the filename of :term:`Trained Model Binary`)



``artifactName`` is the filename of the trained model. Our model is stored in :term:`GPPI<General Python Prediction Interface>` format.
We can download it from storage that is described in ``models-output`` connection (currently this connection
is created on the Legion Platform installation stage, so we have not created this connection above).


.. _tutorials_wine-pack:

#########################
Pack the trained model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data",  "The trained model in :term:`GPPI<General Python Prediction Interface>` :term:`Trained Model Binary Format`"
    "Step output data", "The packed model as Docker image with REST API"

Create payload:

.. code-block:: console

    $ touch ./legion/packaging.legion.yaml


Paste next code to the created file:

.. code-block:: yaml
   :caption: ./legion/packaging.legion.yaml
   :name: ModelPackaging
   :linenos:
   :emphasize-lines: 4, 6-8

    id: wine
    kind: ModelPackaging
    spec:
      artifactName: "<fill-in>"  # set artifact name from previous step;
      targets:
        - connectionName: docker-ci  # set docker repository connection where our packaged model will be saved
          name: docker-push
      integrationName: docker-rest  # set Model packaging toolchain integration as rest service

In this file, we do:

- line 4: Set artifact name from the previous step;
- line 6: Set target docker registry to id from :ref:`Docker connection` file;
- line 7: Set target command for the packager;
- line 8: Set id of :term:`Docker REST API Packaging Toolchain Integration`;

Create :term:`Model Packaging` using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/packaging.legion.yaml

Check :term:`Model Packaging` logs:

.. code-block:: console

    $ legionctl packaging logs --id wine

After some time :term:`Model Packaging` will be finished.

To check status run:

.. code-block:: console

    $ legionctl packaging get --id wine

You will see YAML with updated :term:`Model Packaging` resource. Look at the status section. You can see:

- ``image`` (this is the filename of docker image in the registry with the trained model as a REST service`);


Or create packaging using :term:`Plugin for JupyterLab`:

1. Open jupyterlab;
2. Open cloned repo, and then the folder with the project;
3. Select file ``./legion/packaging.legion.yaml`` and in context menu press ``submit`` button;

You can see model logs using ``Legion cloud mode`` side tab in your Jupyterlab

1. Open ``Legion cloud mode`` tab;
2. Look for ``PACKAGING`` section;
3. Press on the row with `ID=wine`;
4. Press button ``LOGS`` to connect to :term:`Model Packaging` logs;

After some time :term:`Model Packaging` will be finished. Status of training is updated in column ``status`` of the `PACKAGING` section
in the ``Legion cloud mode`` tab. If model training finished with success you will see `status=succeeded`.

Then open :term:`Model Packaging` again by pressing the appropriate row. Look at the `Results` section. You can see:

- ``image`` (this is the filename of docker image in the registry with the trained model as a REST service`);


.. _tutorials_wine-deploy:

#########################
Deploy the packed model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data",  "The packed model as Docker image with REST API"
    "Step output data", "The deployed model"


Create payload:

.. code-block:: console

    $ touch ./legion/deployment.legion.yaml


Paste next code to the created file:

.. code-block:: yaml
   :caption: ./legion/deployment.legion.yaml
   :name: ModelDeployment
   :linenos:
   :emphasize-lines: 4, 6-8

    id: wine
    kind: ModelDeployment
    spec:
      image: "<fill-in>"
      minReplicas: 1
      ImagePullConnectionID: docker-ci

In this file, we do:

- line 4: Set ``image`` that we got on the previous step;
- line 6: Set id of :term:`Docker REST API Packaging Toolchain Integration`;

Create :term:`Model Deploying` using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/deployment.legion.yaml

After some time :term:`Model Deploying` will be finished.

To check status run:

.. code-block:: console

    $ legionctl deployment get --id wine

Or create packaging using :term:`Plugin for JupyterLab`:

1. Open jupyterlab;
2. Open cloned repo, and then the folder with the project;
3. Select file ``./legion/deployment.legion.yaml`` and in context menu press ``submit`` button;

You can see model logs using ``Legion cloud mode`` side tab in your Jupyterlab

1. Open ``Legion cloud mode`` tab;
2. Look for ``DEPLOYMENT`` section;
3. Press on the row with `ID=wine`;

After some time :term:`Model Deploying` will be finished. Status of training is updated in column ``status`` of the `DEPLOYMENT` section
in the ``Legion cloud mode`` tab. If model training finished with success you will see `status=Ready`



.. _tutorials_wine-use:

#########################
Use the deployed model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data",  "The deployed model"

After the model is successfully deployed you can check its API in swagger.

Just open ``edge.<your-legion-platform-host>/swagger/index.html`` and look and next endpoints

1. ``GET /model/wine/api/model/info`` – OpenAPI model specification;
2. ``POST /model/wine/api/model/invoke`` – Endpoint to do predictions;

But you can also do predictions using :term:`Legion CLI`.

Create ``./legion/r.json`` file:

.. code-block:: console

    $ touch ./legion/r.json

Add payload for ``/model/wine/api/model/invoke`` according to OpenAPI schema.
In this payload we list model input variables:

.. code-block:: json
   :caption: ./legion/r.json
   :name: Model invoke payload

   {
     "columns": [
       "fixed acidity",
       "volatile acidity",
       "citric acid",
       "residual sugar",
       "chlorides",
       "free sulfur dioxide",
       "total sulfur dioxide",
       "density",
       "pH",
       "sulphates",
       "alcohol"
     ],
     "data": [
       [
         7,
         0.27,
         0.36,
         20.7,
         0.045,
         45,
         170,
         1.001,
         3,
         0.45,
         8.8
       ]
     ]
   }


Invoke the model to make a prediction:

.. code-block:: console

    $ legionctl model invoke --mr wine --json-file r.json

.. code-block:: json
   :caption: ./legion/r.json
   :name: Model invoke output

   {"prediction": [6.0], "columns": ["quality"]}


Congrats! You have completed the tutorial!
