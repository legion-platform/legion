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
package com.epam.legion.jenkins;

import org.junit.Assert;
import org.junit.Test;

import java.io.File;
import java.io.StringReader;
import java.util.Map;

public class UtilsTest {
    @Test
    public void normalizePropertyName() throws Exception {
        Assert.assertEquals("modelId", Utils.normalizePropertyName("Model-Id"));
        Assert.assertEquals("anotherProperty", Utils.normalizePropertyName("anotherProperty"));
    }

    @Test
    public void scanLogForProperies() throws Exception {
        String sep = System.getProperty("line.separator");

        String log = "Line1" + sep
                + "Line2" + sep
                + "X-Legion-Model-Id:myModel" + sep
                + "Line3" + sep
                + "Line3a://X-Legion-Some-Property:someValue" + sep
                + "Line4" + sep
                + "X-Legion-Model-File-Name:/tmp/folder/myExport.model" + sep
                + "Line5" + sep
                + "Line6" + sep;

        Map<String,String> props = Utils.scanLogForProperties(new StringReader(log));

        Assert.assertEquals("myModel", props.get("modelId"));
        Assert.assertEquals("/tmp/folder/myExport.model", props.get("modelFileName"));
        Assert.assertEquals(2, props.size());
    }

    @Test
    public void getGroovyScriptPath() throws Exception {
        File tmpFile = File.createTempFile("unit", "test");

        File scriptFile = new File(tmpFile.getParent() + File.separator +
                "scripts" + File.separator + "legion.groovy");
        Assert.assertEquals(scriptFile, Utils.getGroovyScriptPath(tmpFile.getParentFile()));
        Assert.assertTrue(scriptFile.exists());

        scriptFile.delete();
        new File(tmpFile.getParentFile(), "scripts").delete();
        tmpFile.delete();
    }
}
