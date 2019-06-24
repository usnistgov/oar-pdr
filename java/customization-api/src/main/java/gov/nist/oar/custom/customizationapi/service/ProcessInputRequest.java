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
package gov.nist.oar.custom.customizationapi.service;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import gov.nist.oar.custom.customizationapi.helpers.JSONUtils;

/**
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class ProcessInputRequest {
    private Logger logger = LoggerFactory.getLogger(ProcessInputRequest.class);

//    // Check the input json data and validate
//    public void parseInputParams(Map<String, String> params) {
//
//	logger.info("In parseInputParams");
//    }

    public boolean validateInputParams(String json) {
	// Add the json schema validation
	if (JSONUtils.isJSONValid(json))
	    return JSONUtils.validateInput(json);
	else
	    return false;
    }

    // Validate input json
    public void validate() {
	logger.info("validate input json againts given properties");
    }

}
