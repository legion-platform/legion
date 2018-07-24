/**
 *   Copyright 2018 EPAM Systems
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

/* eslint-disable func-names */
exports.loadConfig = function () {
    const headElement = document.getElementsByTagName('head')[0];

    // Look up where the Blue Ocean app is hosted
    exports.blueoceanAppURL = headElement.getAttribute('data-appurl');

    if (typeof exports.blueoceanAppURL !== 'string') {
        exports.blueoceanAppURL = '/';
    }

    exports.jenkinsRootURL = headElement.getAttribute('data-rooturl');
};

exports.getJenkinsRootURL = function getJenkinsRootURL() {
    if (!exports.jenkinsRootURL) {
        exports.loadConfig();
    }
    return exports.jenkinsRootURL;
};

exports.getRestRoot = function getRestRoot() {
    return `${exports.getJenkinsRootURL()}/blue/rest`;
};
