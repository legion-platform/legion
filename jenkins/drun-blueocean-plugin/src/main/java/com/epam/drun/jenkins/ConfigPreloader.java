/**
 *   Copyright 2017 EPAM Systems
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
package com.epam.drun.jenkins;

import hudson.Extension;
import io.jenkins.blueocean.commons.PageStatePreloader;
import net.sf.json.util.JSONBuilder;

import java.io.StringWriter;

/*
Basic drun jenkins plugin configuration
 */
@Extension
public class ConfigPreloader extends PageStatePreloader {
    private final static String dashboardUrlPropertyName =
            "com.epam.drun.jenkins.dashboard.url";
    private final static String dashboardUrlPropertyDefault =
            "/grafana/dashboard/script/model_builds.js?orgId=1&theme=light&model=";
    private final static String jupyterHtmlPathPropertyName =
            "com.epam.drun.jenkins.jupyter.html.path";
    private final static String jupyterHtmlPathPropertyDefault =
            "notebook.html";

    @Override
    public String getStatePropertyPath() {
        return "drun";
    }

    @Override
    public String getStateJson() {
        StringWriter writer = new StringWriter();

        new JSONBuilder(writer)
            .object()
                .key("dashboardUrl").value(
                        System.getProperty(dashboardUrlPropertyName, dashboardUrlPropertyDefault))
                .key("jupyterHtmlPath").value(
                        System.getProperty(jupyterHtmlPathPropertyName, jupyterHtmlPathPropertyDefault))
            .endObject();

        return writer.toString();
    }
}
