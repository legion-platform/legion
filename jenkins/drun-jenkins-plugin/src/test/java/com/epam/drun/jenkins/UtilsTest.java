package com.epam.drun.jenkins;

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
                + "X-DRun-Model-Id:myModel" + sep
                + "Line3" + sep
                + "Line3a://X-DRun-Some-Property:someValue" + sep
                + "Line4" + sep
                + "X-DRun-Model-File-Name:/tmp/folder/myExport.model" + sep
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
