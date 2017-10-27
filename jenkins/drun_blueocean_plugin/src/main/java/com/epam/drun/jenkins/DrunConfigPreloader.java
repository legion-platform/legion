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

import java.io.StringWriter;
import hudson.Extension;
import net.sf.json.util.JSONBuilder;
import io.jenkins.blueocean.commons.PageStatePreloader;

/*
Basic drun jenkins plugin configuration
 */
@Extension
public class DrunConfigPreloader extends PageStatePreloader {
    static String dashboardUrl = System.getProperty("com.epam.drun.jenkins.dashboard.url",
            "/grafana/dashboard/db");
    static String jupyterHtmlPath = System.getProperty("com.epam.drun.jenkins.jupyter.html.path",
        "artifact/src/sample.html");

    @Override
    public String getStatePropertyPath() {
        return "drun";
    }

    @Override
    public String getStateJson() {
        StringWriter writer = new StringWriter();

        new JSONBuilder(writer)
            .object()
                .key("dashboardUrl").value(dashboardUrl)
                .key("jupyterHtmlPath").value(jupyterHtmlPath)
            .endObject();

        return writer.toString();
    }
}
