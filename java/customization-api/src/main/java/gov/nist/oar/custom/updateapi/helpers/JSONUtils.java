/**
 * This software was developed at the National Institute of Standards and Technology by employees of
 * the Federal Government in the course of their official duties. Pursuant to title 17 Section 105
 * of the United States Code this software is not subject to copyright protection and is in the
 * public domain. This is an experimental system. NIST assumes no responsibility whatsoever for its
 * use by other parties, and makes no guarantees, expressed or implied, about its quality,
 * reliability, or any other characteristic. We would appreciate acknowledgement if the software is
 * used. This software can be redistributed and/or modified freely provided that any derivative
 * works bear some notice that they are derived from it, and any modified versions bear some notice
 * that they have been modified.
 * @author: Deoyani Nandrekar-Heinis
 */
package gov.nist.oar.custom.updateapi.helpers;

import java.io.IOException;
import java.io.InputStream;

import org.apache.commons.io.IOUtils;
import org.everit.json.schema.Schema;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * JSONUtils class provides some static functions to parse and validate json
 * data.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public final class JSONUtils {

    protected static Logger logger = LoggerFactory.getLogger(JSONUtils.class);

    private JSONUtils() {
	// Default
    }

    /**
     * Read jsonstring to check validity
     * 
     * @param jsonInString
     * @return boolean
     */
    public static boolean isJSONValid(String jsonInString) {
	try {
	    final ObjectMapper mapper = new ObjectMapper();
	    mapper.readTree(jsonInString);
	    return true;
	} catch (IOException e) {
	    logger.error("There is an error validating json:" + e.getMessage());
	    return false;
	}
    }

    public static boolean validateInput(String jsonRequest) {
	try {

	    InputStream inputStream = JSONUtils.class.getClassLoader().getResourceAsStream("static/json-schema.json");
	    String inputSchema = IOUtils.toString(inputStream);
	    JSONObject rawSchema = new JSONObject(new JSONTokener(inputSchema));
	    Schema schema = SchemaLoader.load(rawSchema);
	    schema.validate(new JSONObject(jsonRequest)); // throws a
							  // ValidationException
							  // if this object is
							  // invalid
	    return true;
	} catch (Exception e) {
	    logger.error("There is error validation input against JSON schema:" + e.getMessage());
	    return false;
	}
    }
}
