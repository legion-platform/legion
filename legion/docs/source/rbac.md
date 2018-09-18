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

### Properties system
#### Finding properties in enclave
* `CoreV1Api.list_namespaced_config_map`
* `CoreV1Api.list_namespaced_secret`

#### Reading properties
* `CoreV1Api.read_namespaced_config_map`
* `CoreV1Api.read_namespaced_secret`

#### Writing properties
* `CoreV1Api.replace_namespaced_config_map`
* `CoreV1Api.create_namespaced_config_map`
* `CoreV1Api.replace_namespaced_secret`
* `CoreV1Api.create_namespaced_secret`

#### Watching properties update
* `CoreV1Api.list_namespaced_config_map [WATCH]`
* `CoreV1Api.list_namespaced_secret [WATCH]`

#### Removing properties
* `CoreV1Api.delete_namespaced_config_map`
* `CoreV1Api.delete_namespaced_secret`

## Usage by modules
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
	
##### legion.k8s.enclave.find_enclaves
* `CoreV1Api.list_namespace`

### Services	
##### legion.k8s.services.ModelService._load_data
* `ExtensionsV1beta1Api.list_namespaced_deployment`
	
##### legion.k8s.services.ModelService.scale
* `ExtensionsV1beta1Api.patch_namespaced_deployment`
	
##### legion.k8s.services.ModelService.delete
* `AppsV1beta1Api.delete_namespaced_deployment`
* `CoreV1Api.delete_namespaced_service`

##### legion.k8s.services.find_model_deployment
* `ExtensionsV1beta1Api.list_namespaced_deployment`
	
##### legion.k8s.services.find_all_models_deployments
* `ExtensionsV1beta1Api.list_namespaced_deployment`
* `ExtensionsV1beta1Api.list_deployment_for_all_namespaces`
	
##### legion.k8s.services.find_all_services
* `CoreV1Api.list_namespaced_service`
* `CoreV1Api.list_service_for_all_namespaces`
	
##### legion.k8s.services.find_all_ingresses
* `ExtensionsV1beta1Api.list_namespaced_ingress`
* `ExtensionsV1beta1Api.list_ingress_for_all_namespaces`

### Properties system
##### legion.k8s.properties.K8SConfigMapStorage.list
* `CoreV1Api.list_namespaced_config_map`

##### legion.k8s.properties.K8SConfigMapStorage.watch
* `CoreV1Api.list_namespaced_config_map [WATCH]`

#### legion.k8s.properties.K8SConfigMapStorage.load
Or on any read data access before first load. Or on read data access after Cache TTL timeout.
* `CoreV1Api.read_namespaced_config_map`

#### legion.k8s.properties.K8SConfigMapStorage.save
* `CoreV1Api.replace_namespaced_config_map`
* `CoreV1Api.create_namespaced_config_map`

#### legion.k8s.properties.K8SConfigMapStorage.destroy
* `CoreV1Api.delete_namespaced_config_map`

##### legion.k8s.properties.K8SSecretStorage.list
* `CoreV1Api.list_namespaced_secret`

##### legion.k8s.properties.K8SSecretStorage.watch
* `CoreV1Api.list_namespaced_secret [WATCH]`

#### legion.k8s.properties.K8SSecretStorage.load
Or on any read data access before first load. Or on read data access after Cache TTL timeout.
* `CoreV1Api.read_namespaced_secret`

#### legion.k8s.properties.K8SSecretStorage.save
* `CoreV1Api.replace_namespaced_secret`
* `CoreV1Api.create_namespaced_secret`

#### legion.k8s.properties.K8SSecretStorage.destroy
* `CoreV1Api.delete_namespaced_secret`