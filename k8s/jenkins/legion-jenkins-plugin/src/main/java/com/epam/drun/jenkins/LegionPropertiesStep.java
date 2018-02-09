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
package com.epam.legion.jenkins;

import java.util.*;

import hudson.Extension;
import hudson.model.Run;
import net.sf.json.JSONObject;
import org.jenkinsci.plugins.workflow.steps.*;
import org.kohsuke.stapler.DataBoundConstructor;

public class LegionPropertiesStep extends Step {

    @DataBoundConstructor public LegionPropertiesStep() { }

    @Override
    public StepExecution start(StepContext context) throws Exception {
        return new Execution(context);
    }

    @Extension
    public static class DescriptorImpl extends StepDescriptor {
        @Override
        public String getFunctionName() {
            return "legionProperties";
        }

        @Override
        public String getDisplayName() {
            return "Returns Legion property map for model and other entities";
        }

        @Override
        public boolean isAdvanced() {
            return true;
        }

        @Override
        public Set<? extends Class<?>> getRequiredContext() {
            return Collections.emptySet(); // depends on the instance
        }
    }

    public static class Execution extends SynchronousStepExecution<Object> {
        private static final long serialVersionUID = 1;

        Execution(StepContext context) {
            super(context);
        }

        @Override
        protected Object run() throws Exception {
            Run run = getContext().get(Run.class);

            return Utils.getProperties(run.getLogReader());
        }
    }
}
