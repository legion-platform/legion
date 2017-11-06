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
import hudson.model.Action;
import hudson.model.Run;
import jenkins.model.TransientActionFactory;

import javax.annotation.Nonnull;
import java.util.Collection;
import java.util.Collections;

@Extension
public class ModelActionFactory extends TransientActionFactory<Run> {
    @Override
    public Class type() {
        return Run.class;
    }

    @Nonnull
    @Override
    public Collection<? extends Action> createFor(@Nonnull Run obj) {
        return Collections.singleton(new ModelAction(obj));
    }
}
