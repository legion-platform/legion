/**
 *   Copyright 2019 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */
import { ServerConnection } from '@jupyterlab/services';
import {
  LEGION_OAUTH_TOKEN_COOKIE_NAME,
  PLUGIN_CREDENTIALS_STORE_TOKEN
} from '../models/apiState';
import ResponseError = ServerConnection.ResponseError;

const HTTP_STATUS_CODE_FORBIDDEN = 403;

export function legionHttpExceptionHandler() {
  return (
    target: any,
    propertyKey: string,
    descriptor: TypedPropertyDescriptor<(...params: any[]) => Promise<any>>
  ) => {
    let oldFunc = descriptor.value;
    descriptor.value = async function() {
      try {
        return await oldFunc.apply(this, arguments); // tslint:disable-line
      } catch (err) {
        // If we get 403 from legion plugin then the token is obsolete.
        if (
          err instanceof ResponseError &&
          err.response.status === HTTP_STATUS_CODE_FORBIDDEN
        ) {
          // Cleanup legion token from local storage store
          localStorage.removeItem(PLUGIN_CREDENTIALS_STORE_TOKEN);
          // Cleanup legion token from cookie
          document.cookie = `${LEGION_OAUTH_TOKEN_COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        }

        throw new ServerConnection.NetworkError(err);
      }
    };
  };
}
