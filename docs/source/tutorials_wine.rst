
====================
MLFlow
====================

In this tutorial you will learn how to Train, Package and Deploy a model from scratch on Legion. Once deployed, the model serves RESTful requests, and makes a prediction when provided user input.

Legion's :ref:`EDI <edi-server-description>` server performs Train, Package, and Deploy operations for you, using its REST API.

.. _tutorials_wine-req:

~~~~~~~~~~~~~~~~~~~
Prerequisites
~~~~~~~~~~~~~~~~~~~

- Legion cluster (:ref:`installation <installation-prereqs>`)
- :ref:`MLFlow <mod_dev_using_mlflow-section>` and :term:`REST API Packager` (installed by default)
- :term:`Legion CLI` or :term:`Plugin for JupyterLab` (installation instructions: :ref:`CLI <legion_cli-install>`, :ref:`Plugin <jupyter_plugin-install>`)
- JWT token from EDI (:ref:`instructions <edi-server-auth>`)
- Google Cloud Storage bucket on Google Compute Platform
- GitHub repository and an ssh key to connect to it

~~~~~~~~~~~~~~~~~~~
Tutorial
~~~~~~~~~~~~~~~~~~~

In this tutorial, you will learn how to:

1. :ref:`Create an MLFlow project <tutorials_wine-create-project>`
2. :ref:`Setup Connections <tutorials_wine-manage-connections>`
3. :ref:`Train a model <tutorials_wine-train>`
4. :ref:`Package the model <tutorials_wine-pack>`
5. :ref:`Deploy the packaged model <tutorials_wine-deploy>`
6. :ref:`Use the deployed model <tutorials_wine-use>`

This tutorial uses a dataset to predict the quality of the wine based on quantitative features
like the wine’s *fixed acidity*, *pH*, *residual sugar*, and so on.
The dataset is from `UCI’s machine learning repository <https://archive.ics.uci.edu/ml/datasets/Wine+Quality>`_.

Code for the tutorial is available on `GitHub <https://github.com/legion-platform/legion-examples/tree/master/mlflow/sklearn/wine>`_.

.. _tutorials_wine-create-project:

#########################
Create MLFlow project
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Before", "Legion cluster that meets :ref:`prerequisites<tutorials_wine-req>`"
    "After", "Model code that predicts wine quality"

Create a new project folder:

.. code-block:: console

   $ mkdir wine && cd wine

Create a training script:

.. code-block:: console

   $ touch train.py

Paste code into the file:

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

In this file, we:

- Start MLflow context on line 46
- Train ``ElasticNet`` model on line 48
- Set metrics, parameters and tags on lines 59-64
- Save model with name ``model`` (model is serialized and sent to the MLflow engine) on line 66
- Save input and output samples (for persisting information about input and output column names) on lines 69-72


Create an MLproject file:

.. code-block:: console

   $ touch MLproject

Paste code into the file:

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

    *Read more about MLproject structure on the* `official MLFlow docs <https://www.mlflow.org/docs/latest/projects.html>`_.


Create a conda environment file:

.. code-block:: console

   $ touch conda.yaml

Paste code to the created file:

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

    All python packages that are used in training script must be listed in the conda.yaml file.

    *Read more about conda environment on the* `official conda docs <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_.

Download the wine data set:

.. code-block:: console

   $ mkdir ./data
   $ wget https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv -O ./data/wine-quality.csv

After this step the project folder should look like this:

.. code-block:: text

    .
    ├── MLproject
    ├── conda.yaml
    ├── data
    │   └── wine-quality.csv
    └── train.py


.. _tutorials_wine-manage-connections:

###################################
Setup connections
###################################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Before", "Legion cluster that meets :ref:`prerequisites<tutorials_wine-req>`"
    "After", "Legion cluster with :term:`Connections<Connection>`"

Legion Platform uses the concept of :term:`Connections<Connection>` to manage authorizations to external services and data.

This tutorial requires three Connections:

- A GitHub repository, where the code is located
- A Google Cloud Storage folder, where input data is located (wine-quality.csv)
- A Docker registry, where the trained and packaged model will be stored for later use

Create a :term:`Connection` to GitHub repository
---------------------------------------------

Because `legion-examples <https://github.com/legion-platform/legion-examples>`_ repository already contains the required code
we will just use this repository. But feel free to create and use a new repository if you want.

Legion is REST-powered, and so we encode the REST "payloads" in this tutorial in YAML files. Create a directory where payloads files will be staged:

.. code-block:: console

    $ mkdir ./legion

Create payload:

.. code-block:: console

    $ touch ./legion/vcs_connection.legion.yaml

Paste code into the created file:

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

Create a Connection using the :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/vcs_connection.legion.yaml

Or create a Connection using :term:`Plugin for JupyterLab`:

1. Open jupyterlab (available by jupyterlab.<your-cluster-base-address>);
2. Open cloned repo, and then the folder with the project;
3. Select file ``./legion/vcs_connection.legion.yaml`` and in context menu press ``submit`` button;


Create :term:`Connection` to wine-quality.csv object storage
-------------------------------------------------------------

Create payload:

.. code-block:: console

    $ touch ./legion/wine_connection.legion.yaml

Paste this code into the file:

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

Create a connection using the :term:`Legion CLI` or :term:`Plugin for JupyterLab`, as in the previous example.

If wine-quality.csv is not in the GCS bucket yet, use this command:

.. code-block:: console

    $ gsutil cp ./data/wine-quality.csv gs://<bucket-name>/data/


Create a :term:`Connection` to a docker registry
------------------------------------------------

Create payload:

.. code-block:: console

    $ touch ./legion/docker_connection.legion.yaml

Paste this code into the file:

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


Create the connection using :term:`Legion CLI` or :term:`Plugin for JupyterLab`, as in the previous example.

Check that all Connections were created successfully:

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

Congrats! You are now ready to train the model.

.. _tutorials_wine-train:

##############################
Train the model
##############################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Before", "Project code, hosted on GitHub"
    "After", "Trained :term:`GPPI<General Python Prediction Interface>` model (a :term:`Trained Model Binary`)"

Create payload:

.. code-block:: console

    $ touch ./legion/training.legion.yaml

Paste code into the file:

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
      workDir: mlflow/sklearn/wine  # MLproject location (in GitHub)
      data:
        - connName: wine
          localPath: mlflow/sklearn/wine/wine-quality.csv # wine-quality.csv file (on GCS)
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

In this file, we:

- line 7: Set Legion toolchain's name to :ref:`mlflow <mod_dev_using_mlflow-section>`
- line 8: Reference ``main`` method in ``entry_points`` (which is defined for :ref:`MLproject files <MLproject file>`.
- line 9: Point ``workDir`` to the MLFlow project directory. (This is the directory that has the :ref:`MLproject file` in it.)
- line 10: A section defining input data
- line 11: ``connName`` id of the :ref:`Wine connection` (created in the previous step)
- line 12: ``localPath`` relative path of the data file
- lines 13-14: Input hyperparameters, defined in MLProject file, and passed to ``main`` method
- line 22: ``vcsName`` id of the :ref:`VCS Connection` (created in the previous step)

:term:`Train` using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/training.legion.yaml

Check :term:`Train` logs:

.. code-block:: console

    $ legionctl training logs --id wine

The :term:`Train` process will finish after some time.

To check the status run:

.. code-block:: console

    $ legionctl training get --id wine

When the Train process finishes, the command will output this YAML:

- ``state`` succeeded
- ``artifactName`` (filename of :term:`Trained Model Binary`)


Or `Train` using the :term:`Plugin for JupyterLab`:

1. Open jupyterlab
2. Open cloned repo, and then the folder with the project
3. Select file ``./legion/training.legion.yaml`` and in context menu press ``submit`` button

You can see model logs using ``Legion cloud mode`` in the left side tab (cloud icon) in Jupyterlab

1. Open ``Legion cloud mode`` tab
2. Look for ``TRAINING`` section
3. Press on the row with `ID=wine`
4. Press button ``LOGS`` to connect to :term:`Train` logs

After some time, the :term:`Train` process will finish. Train status is updated in column ``status`` of the `TRAINING` section
in the ``Legion cloud mode`` tab. If the model training finishes with success, you will see `status=succeeded`.

Then open :term:`Train` again by pressing the appropriate row. Look at the `Results` section. You should see:

- ``artifactName`` (filename of :term:`Trained Model Binary`)


``artifactName`` is the filename of the trained model. This model is in :term:`GPPI<General Python Prediction Interface>` format.
We can download it from storage defined in the ``models-output`` Connection.  (This connection is created during Legion Platform installation, so we were not required to create this Connection as part of this tutorial.)


.. _tutorials_wine-pack:

#########################
Package the model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Before",  "The trained model in :term:`GPPI<General Python Prediction Interface>` :term:`Trained Model Binary`"
    "After", "Docker image for the packaged model, including a model REST API"

Create payload:

.. code-block:: console

    $ touch ./legion/packaging.legion.yaml

Paste code into the file:

.. code-block:: yaml
   :caption: ./legion/packaging.legion.yaml
   :name: ModelPackaging
   :linenos:
   :emphasize-lines: 4, 6-8

    id: wine
    kind: ModelPackaging
    spec:
      artifactName: "<fill-in>"  # Use artifact name from Train step
      targets:
        - connectionName: docker-ci  # Docker registry when output image will be stored
          name: docker-push
      integrationName: docker-rest  # REST API Packager

In this file, we:

- line 4: Set to artifact name from the Train step
- line 6: Set to docker registry, where output will be staged
- line 7: Specify the docker command
- line 8: id of the :term:`REST API Packager`

Create a :term:`Package` using :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/packaging.legion.yaml

Check the :term:`Package` logs:

.. code-block:: console

    $ legionctl packaging logs --id wine

After some time, the :term:`Package` process will finish.

To check the status, run:

.. code-block:: console

    $ legionctl packaging get --id wine

You will see YAML with updated :term:`Package` resource. Look at the status section. You can see:

- ``image`` # This is the filename of the Docker image in the registry with the trained model prediction, served via REST`.

Or run Package using the :term:`Plugin for JupyterLab`:

1. Open jupyterlab
2. Open the repository that has the source code, and navigate to the folder with the MLProject file
3. Select file ``./legion/packaging.legion.yaml`` and in the context menu press the ``submit`` button

To view Package logs, use ``Legion cloud mode`` in the side tab of your Jupyterlab

1. Open ``Legion cloud mode`` tab
2. Look for ``PACKAGING`` section
3. Click on the row with `ID=wine`
4. Click the button for ``LOGS`` and view the ``Packaging`` logs

After some time, the :term:`Package` process will finish. The status of training is updated in column ``status`` of the `PACKAGING` section in the ``Legion cloud mode`` tab. You should see `status=succeeded`.

Then open PACKAGING again by pressing the appropriate row. Look at the `Results` section. You should see:

- ``image`` (this is the filename of docker image in the registry with the trained model as a REST service`);

.. _tutorials_wine-deploy:

#########################
Deploy the model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Before",  "Model is packaged as image in the Docker registry"
    "After", "Model is served via REST API from the Legion cluster"

Create payload:

.. code-block:: console

    $ touch ./legion/deployment.legion.yaml


Paste code into the file:

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

In this file, we:

- line 4: Set the ``image`` that was created in the Package step
- line 6: Set the id of the :term:`REST API Packager`

Create a :term:`Deploy` using the :term:`Legion CLI`:

.. code-block:: console

    $ legionctl conn create -f ./legion/deployment.legion.yaml

After some time, the :term:`Deploy` process will finish.

To check its status, run:

.. code-block:: console

    $ legionctl deployment get --id wine

Or create a `Deploy` using the :term:`Plugin for JupyterLab`:

1. Open jupyterlab
2. Open the cloned repo, and then the folder with the MLProject file
3. Select file ``./legion/deployment.legion.yaml``. In context menu press the ``submit`` button

You can see Deploy logs using the ``Legion cloud mode`` side tab in your Jupyterlab

1. Open the ``Legion cloud mode`` tab
2. Look for the ``DEPLOYMENT`` section
3. Click the row with `ID=wine`

After some time, the :term:`Deploy` process will finish. The status of Deploy is updated in column ``status`` of the `DEPLOYMENT` section in the ``Legion cloud mode`` tab. You should see `status=Ready`.

.. _tutorials_wine-use:

#########################
Use the deployed model
#########################

.. csv-table::
   :stub-columns: 1
   :width: 100%

    "Step input data",  "The deployed model"

After the model is deployed, you can check its API in Swagger:

Open ``<your-legion-platform-host>/swagger/index.html`` and look and the endpoints:

1. ``GET /model/wine/api/model/info`` – OpenAPI model specification;
2. ``POST /model/wine/api/model/invoke`` – Endpoint to do predictions;

But you can also do predictions using the :term:`Legion CLI`.

Create a payload file:

.. code-block:: console

    $ touch ./legion/r.json

Add payload for ``/model/wine/api/model/invoke`` according to the OpenAPI schema. In this payload we provide values for model input variables:

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


Congrats! You have completed the tutorial.
