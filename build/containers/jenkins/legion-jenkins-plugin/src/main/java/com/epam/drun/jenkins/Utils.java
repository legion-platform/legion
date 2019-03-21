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

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import net.sf.json.JSONObject;

import java.io.*;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

public class Utils {
    private static final Logger log = Logger.getLogger( Utils.class.getName() );

    //Sample Header style log entry: X-Legion-Model-Id:Model_1
    private static final String LEGION_PROPERTY_PREFIX = "X-Legion-";
    public static final String LEGION_SCRIPTS_PATH = "scripts";
    public static final String LEGION_SCRIPT_NAME = "legion.groovy";

    public static JSONObject getJson(Reader reader) throws IOException {
        JSONObject json = new JSONObject();

        Map<String,String> props = scanLogForProperties(reader);
        for(Map.Entry<String,String> entry : props.entrySet()) {
            json.put(entry.getKey(), entry.getValue());
        }

        return json;
    }

    public static Map getProperties(Reader reader) throws IOException {
        return scanLogForProperties(reader);
    }

    /**
     * Search log for properties
     * @param reader
     * @return
     */
    public static Map<String,String> scanLogForProperties(Reader reader) throws IOException {
        Map props = new HashMap<String,String>();

        BufferedReader r = new BufferedReader(reader);
        for(String line = r.readLine(); line != null; ) {
            if(line.startsWith(LEGION_PROPERTY_PREFIX)) {
                String propName = normalizePropertyName(
                        line.substring(LEGION_PROPERTY_PREFIX.length(), line.indexOf(':')));
                String propValue = line.substring(line.indexOf(':') + 1);

                props.put(propName, propValue);
            }

            line = r.readLine();
        }
        r.close();

        return props;
    }

    /**
     * Removes '-' and makes camel case by lower-casing first letter
     * @param key
     * @return
     */
    public static String normalizePropertyName(String key)
    {
        String s = key.replace("-", "");

        return s.substring(0, 1).toLowerCase() + s.substring(1);
    }

    /**
     * Get Legion script name from the environment variable
     * @return
     */
    @SuppressFBWarnings(justification="Internal file handling ",
            value={"RV_RETURN_VALUE_IGNORED_BAD_PRACTICE", "DM_DEFAULT_ENCODING"})
    public static File getGroovyScriptPath(File workDir) throws IOException
    {
        InputStream resFile = Utils.class.getClassLoader().getResourceAsStream(LEGION_SCRIPT_NAME);
        File scriptDir = new File(workDir, LEGION_SCRIPTS_PATH);
        if (!scriptDir.exists()) scriptDir.mkdir();
        File scriptFile = new File(scriptDir, LEGION_SCRIPT_NAME);

        BufferedReader reader = new BufferedReader(new InputStreamReader(resFile));
        BufferedWriter writer = new BufferedWriter(new FileWriter(scriptFile));

        String line = reader.readLine();
        while (line != null){
            writer.write(line + System.lineSeparator());
            line = reader.readLine();
        }
        writer.close();
        reader.close();

        return scriptFile;
    }
}
