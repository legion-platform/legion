## Jenkins

# General

Uses for running models tests. 
Contains a main job `legion-examples` that scans github repository legion-examples and
creates a new job for each founded Jenkinsfile.

* Access URL: [parallels/jenkins](http://parallels/jenkins)
* Authorisation: **admin** / **admin**

# Jenkins Plugin

Prerequisites for building the plugin
* Java 1.7
* Maven 3.3.9+
* Node 6.4.0+
* npm 3.10.3+

Building & Running
* clone repo
* Run "mvn clean install hpi:run"
* Goto localhost:8080, and setup Jenkins using secret key; create admin/admin user
* Goto to Configure/Manage Plugins and update all plugins; they will remain pinned
