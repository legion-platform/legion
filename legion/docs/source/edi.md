# Edi

Edi is a Flask-based RESTful API that can manage Models.
It's used by **legionctl** via **EdiClient**.

It supportes next functionality:
* **deploy** - Deploy a Model API endpoint:
    * Endpoint: */api/1.0/deploy*
    * Method: *POST*
    * Parameters:
        * **k8s_image** - (Required, if **image** is empty) Docker image for kubernetes deployment;
        * **image** - (Omitted, if **k8s_image** exists) Docker image for deploy (for kubernetes deployment and local pull);
        * **count** - (Optional, default=1) Desired number of Pods.

2. **undeploy** - Undeploy a Model API endpoint
    * Endpoint: */api/1.0/undeploy*
    * Method: *POST*
    * Parameters:
        * **model** - Model Id of a model to undeploy;
        * **grace_period** - Grace period for removing, should be a non-negative value. Zero value idicates to delete immediately.

3. **scale** - Scale a Model API endpoint
    * Endpoint: */api/1.0/scale*
    * Method: *POST*
    * Parameters:
        * **model** - Model Id of a model to scale;
        * **count** - Desired number of Pods.

4. **inspect** - Get details about all the Model API Endpoints: name, version, image path, status and etc.
    * Endpoint: */api/1.0/inspect*
    * Method: *GET*
    * Sample Response:
        ```json
        [
          {
            "deployment": "deployment",
            "image": "localhost:31111/legion_model/test-summation:1.0-180504190034.2.6463943",
            "model": "test-summation",
            "model_api_info": {
              "host": "http://legion-company-a-edge.company-a.svc.cluster.local:80",
              "result": {
                "input_params": false,
                "use_df": false,
                "version": "1.0"
              }
            },
            "model_api_ok": true,
            "namespace": "company-a",
            "ready_replicas": 1,
            "scale": 1,
            "status": "ok",
            "version": "1.0"
          }
        ]
        ```

5. **info** - Get cluster state details: host names of services in a cluster namespace.
    * Endpoint: */api/1.0/info*
    * Method: *GET*
    * Sample Response:
        ```json
        {
          "deployment": "legion-company-a",
          "domain": "-company-a.legion-dev.epm.kharlamov.biz",
          "edge": {
            "domain": "legion-company-a-edge.company-a.svc.cluster.local",
            "port": 80,
            "public": "edge-company-a.legion-dev.epm.kharlamov.biz"
          },
          "enclave": "company-a",
          "grafana": {
            "domain": "legion-company-a-grafana.company-a.svc.cluster.local",
            "port": 80,
            "public": "grafana-company-a.legion-dev.epm.kharlamov.biz"
          },
          "graphite": {
            "domain": "legion-company-a-graphite.company-a.svc.cluster.local",
            "port": 8125
          },
          "jupyter": {
            "public": "nfs-company-a.legion-dev.epm.kharlamov.biz"
          },
          "ldap": {
            "public": "ldap-company-a.legion-dev.epm.kharlamov.biz"
          },
          "namespace": "company-a"
        }
        ```


