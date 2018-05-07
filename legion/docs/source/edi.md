# Edi

Edi is a Flask-based RESTful API that can manage Models.
It's used by **legionctl** via **EdiClient**.

It supportes next functionality:
* **deploy** - Deploy a Model API endpoint:
    * Endpoint: */api/1.0/deploy*
    * Method: *POST*
    * Parameters:
        * **image** - Docker image for deploy (for jybernetes deployment and local pull)
        * **k8s_image** - (Optional) Docker image for kubernetes deployment
        * **count** - (Optional) Number of Pods to create

2. **undeploy** - Undeploy a Model API endpoint
    * Endpoint: */api/1.0/undeploy*
    * Method: *POST*
    * Parameters:
        * **model** - Model Id
        * **grace_period** - Grace period for removing

3. **scale** - Scale a Model API endpoint
    * Endpoint: */api/1.0/scale*
    * Method: *POST*
    * Parameters:
        * **model** - Model Id
        * **count** - Number of pods to create

4. **inspect** - Collect details about all the Model API Endpoints
    * Endpoint: */api/1.0/inspect*
    * Method: *GET*

5. **info** - Get cluster state details
    * Endpoint: */api/1.0/info*
    * Method: *GET*


