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

export interface TrainingResult {
    /**
     * Trained artifact name
     */
    artifactName?: string;

    /**
     * VCS commit
     */
    commitID?: string;

    /**
     * Mlflow run ID
     */
    runId?: string;

}
