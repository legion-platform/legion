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

import hudson.model.Action;
import hudson.model.Run;
import net.sf.json.JSONObject;
import org.kohsuke.stapler.WebMethod;
import org.kohsuke.stapler.export.Exported;
import org.kohsuke.stapler.export.ExportedBean;

import javax.annotation.CheckForNull;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.logging.Level;
import java.util.logging.Logger;

@ExportedBean
public class ModelAction implements Action {
    private static final Logger log = Logger.getLogger( ModelAction.class.getName() );
    private Run job;

    public ModelAction(Run job) {
        this.job = job;
    }

    @CheckForNull
    @Override
    public String getIconFileName() {
        return "notepad.png";
    }

    @CheckForNull
    @Override
    public String getDisplayName() {
        return "Model Json";
    }

    @CheckForNull
    @Override
    public String getUrlName() {
        return "model";
    }

    @WebMethod (name = "json")
    @Exported (name = "modelJson")
    public final String getJson() throws IOException {
        return Utils.getJson(job.getLogReader()).toString();
    }

}
