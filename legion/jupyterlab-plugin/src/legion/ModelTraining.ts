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

export interface ModelTraining {
    /**
     * Model training ID
     */
    id?: string;

    /**
     * Model training specification
     */
    spec?: models.ModelTrainingSpec;

    /**
     * Model training status
     */
    status?: models.ModelTrainingStatus;

}