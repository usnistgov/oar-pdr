package gov.nist.oar.custom.customizationapi.helpers;
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


import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.ExpectedException;


import gov.nist.oar.custom.customizationapi.exceptions.InvalidInputException;

/**
 * Test JSONUtils class which checks valid JSON and also validates input against given JSON schema.
 * @author Deoyani Nandrekar-Heinis
 *
 */


public class JSONUtilsTest {


    @Rule
    public final ExpectedException exception = ExpectedException.none();

    @Test
    public void isJSONValidTest() throws InvalidInputException {
	String testJson = "{\"title\" : \"New Title Update\",\"description\": \"new description update\"}";

	assertTrue(JSONUtils.isJSONValid(testJson));
	testJson = "{\"title\" : \"New Title Update\",description: \"new description update\"}";
	assertTrue(JSONUtils.isJSONValid(testJson));
	testJson = "{\"jnsfhshdjsjk\"}";
	exception.expect(InvalidInputException.class);
	assertFalse(JSONUtils.isJSONValid(testJson));
    }

    @Test
    public void isValidateInput() throws InvalidInputException {
	String testJSON = "{\"title\" : \"New Title Update\",\"description\": \"new description update\"}";
	exception.expect(InvalidInputException.class);
	assertFalse(JSONUtils.validateInput(testJSON));
	

	testJSON = "{\"title\" : \"New Title Update\",\"description\": [\"new description update\"]}";
	assertTrue(JSONUtils.validateInput(testJSON));
//	testJSON = "{\"jnsfhshdjsjk\" : \"New Title Update\",\"description\": \"new description update\"}";
//	assertFalse(JSONUtils.validateInput(testJSON));
	testJSON = "{\"jnsfhshdjsjk\"}";
	exception.expect(InvalidInputException.class);
	assertFalse(JSONUtils.validateInput(testJSON));
	
    }
}
