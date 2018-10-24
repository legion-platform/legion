![LegionLogo](docs/images/legion-logo-h.png)

## Overview

Legion is a resilient AI Runtime platform to run AI Learning models in production.
It was build around the idea of having flexible unified environment for research and production as well as streamlined process of 
delivering those models into production, monitoring their performance, identifying possible mistakes and tracing them back to the source code.

Legion provides: 

* Effortless out-of-the-box CI/CD process, including integrated model quality control with automated retraining and regression testing.
* Cloud-agnostic AI toolchains integrated with the most popular Sklearn, Tensorflow, Spark, R.
* Integrated feedback loop for the input and output capturing, A/B testing and traffic management support.

## Technologies	

* Python 3.6
* Ansible
* Docker
* Kubernetes
* Jenkins
* Airflow
* Nexus
* Graphana
* Graphite
* Prometeus
* Flask
* NGinx

### ML/AI Toolchains:

* Sklearn
* Tensorflow (not supported yet)
* Spark (not supported yet)
* R (not supported yet)
	
## Documentation
* [Model REST API](legion/docs/source/model_rest_api.md)

##  Release workflow:
-	When the decision made about release preparation no PRs should be merged to develop branch until the end of process
-	Build_Legion_Stable_Artifacts job is used for public release creation
-	The job performs next actions some of which could be optionally disabled:
    1.	Pull codebase from Develop branch 
    2.	Set git tag with release version and push it to Github. 
        If such tag exists the job will fail with notice but optionally the tag can be updated. 
    3.	Set version string and artifact’s metadata for python package
    4.	Build documentation
    5.	Run python tests and code analyzers
    6.	Build Legion python packages and upload them both to local and pypi.org repositories
    7.	Build Jenkins plugin for Jenkins Docker image
    8.	Build Docker images and push them both to local and remote Docker repositories
        Latest tag will be updated pointing to the current images
    9.	Increment version string for Legion python package
    10.	Push changes from develop to master branch

## Contact Us
If you are interested in contribution to Legion feel free to create a pull request or create an issue report.
If you interested in hearing more about Legion implementation, existing case studies, questions or concerns feel free to email us at [info@legion-platform.org](mailto:info@legion-platform.org).
