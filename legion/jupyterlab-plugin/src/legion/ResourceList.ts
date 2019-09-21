/**
 * API's Gateway
 * This is a API's Gateway server.
 *
 * OpenAPI spec version: 1.0
 * 
 *
 * NOTE: This class is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 */

import * as models from './models';

export interface ResourceList {
    /**
     * Read more about CPU resource here https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-cpu
     */
    cpu?: string;

    /**
     * Read more about GPU resource here https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/#using-device-plugins
     */
    gpu?: string;

    /**
     * Read more about memory resource here https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/#meaning-of-memory
     */
    memory?: string;

}
