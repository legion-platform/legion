# RBAC configuration
Legion package can be used for introspection and modification of Legion state in K8S cluster.


## Usage K8S API by functionality
### Enclave
#### Listing
* `CoreV1Api.list_namespace`

#### Deploying new models
* `CoreV1Api.list_namespaced_service`
* `ExtensionsV1beta1Api.list_namespaced_deployment`
* `ExtensionsV1beta1Api.create_namespaced_deployment`
* `CoreV1Api.create_namespaced_service`

#### Inspecting 
This function is used to getting models and services in enclave
* `CoreV1Api.list_namespaced_service`

#### Watching models
* `CoreV1Api.list_namespaced_service [WATCH]`

#### Watch enclaves
* `CoreV1Api.list_namespace [WATCH]`

### Service
#### Listing
This functionality implemented in Enclave Inspecting
* `CoreV1Api.list_namespaced_service`

#### Accessing public URL 
This function will be called on accessing public URL for service, uses in EDI to get EDI info
* `ExtensionsV1beta1Api.list_namespaced_ingress`

#### Inspecting models 
This function will be called on access deployment, scale, desired scale, status, image
* `ExtensionsV1beta1Api.list_namespaced_deployment`

#### Scaling models
* `ExtensionsV1beta1Api.patch_namespaced_deployment`

#### Deleting models
* `AppsV1beta1Api.delete_namespaced_deployment`
* `CoreV1Api.delete_namespaced_service`

## Usage by modules
### Utils
##### legion.k8s.utils.find_model_deployment
* `ExtensionsV1beta1Api.list_namespaced_deployment`
	
##### legion.k8s.utils.find_all_models_deployments
* `ExtensionsV1beta1Api.list_namespaced_deployment`
* `ExtensionsV1beta1Api.list_deployment_for_all_namespaces`
	
##### legion.k8s.utils.find_all_services
* `CoreV1Api.list_namespaced_service`
* `CoreV1Api.list_service_for_all_namespaces`
	
##### legion.k8s.utils.find_all_ingresses
* `ExtensionsV1beta1Api.list_namespaced_ingress`
* `ExtensionsV1beta1Api.list_ingress_for_all_namespaces`
	
##### legion.k8s.utils.find_enclaves
* `CoreV1Api.list_namespace`

### Enclaves	
##### legion.k8s.enclave.Enclave.deploy_model
* `ExtensionsV1beta1Api.create_namespaced_deployment`
* `CoreV1Api.create_namespaced_service`
	
##### legion.k8s.enclave.Enclave.watch_services
* `CoreV1Api.list_namespaced_service [WATCH]`
	
##### legion.k8s.enclave.Enclave.watch_enclaves
* `CoreV1Api.list_namespace [WATCH]`
	
##### legion.k8s.enclave.Enclave.delete
* `CoreV1Api.delete_namespace`

### Services	
##### legion.k8s.services.ModelService._load_data
* `ExtensionsV1beta1Api.list_namespaced_deployment`
	
##### legion.k8s.services.ModelService.scale
* `ExtensionsV1beta1Api.patch_namespaced_deployment`
	
##### legion.k8s.services.ModelService.delete
* `AppsV1beta1Api.delete_namespaced_deployment`
* `CoreV1Api.delete_namespaced_service`
