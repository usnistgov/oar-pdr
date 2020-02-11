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
package gov.nist.oar.customizationapi.service;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.helpers.JSONUtils;

/**
 * Validate input parameters to check if its valid json and passes schema test.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class ProcessInputRequest {
	private Logger logger = LoggerFactory.getLogger(ProcessInputRequest.class);

	/**
	 * Added this functionality to process input json string
	 * 
	 * @param json
	 * @return
	 * @throws IOException
	 * @throws InvalidInputException
	 */
	public boolean validateInputParams(String json) throws IOException, InvalidInputException {
		logger.info("Validating input parameteres in the ProcessInputRequest class.");
		// validate JSON and Validate schema against json-customization schema
		return JSONUtils.validateInput(json);

	}

}
