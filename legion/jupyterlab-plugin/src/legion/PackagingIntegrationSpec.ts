/**
 * EDI API
 * This is a EDI server.
 *
 * OpenAPI spec version: 1.0
 * 
 *
 * NOTE: This class is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 */

import * as models from './models';

export interface PackagingIntegrationSpec {
    /**
     * Default packaging Docker image
     */
    defaultImage?: string;

    /**
     * Path to binary which starts a packaging process
     */
    entrypoint?: string;

    /**
     * Enable docker privileged flag
     */
    privileged?: boolean;

    /**
     * Schema which describes targets and arguments for specific packaging integration
     */
    schema?: models.Schema;

}