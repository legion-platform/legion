# What is a model?

Model, in terms of legion may be represented in 2 ways:
* Source code of models, that is stored on Git server. This code uses appropriate toolchains and calls Legion's API for exporting functions.
* Built model (almost all during this documentation term **model** means **built model**). Its structure is defined [below](#build-model).

## Source code of model
Source code of model should use appropriate [toolchain](./tlch_about.md). Some examples, what calls should be done, given in [the examples folder](https://github.com/legion-platform/legion/tree/develop/examples).

## Built model
Model (built model) -- Docker Image that is built using [cluster training](./gs_training_model.md) or [local training](./gs_local_run.md) mode.

It consists of:
* Base (Legion's) layer with all required dependencies (Python 3.6, Legion package and its dependencies)
* Source code of trained model
* Captured state and serialized functions (that have been captured after finishing of training process)
* HTTP serving agent (uWSGI) and its configuration

### Can it be created manually?

Manual model image creation (not on cluster or not using `legionctl` tool) is not recommended, but it's possible. Manual created image should provide appropriate web API (model's protocol) and health-check API on specific port and contains Legion's headers.