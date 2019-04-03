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

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/**
 * @author Deoyani Nandrekar-Heinis
 *
 */

public class JSONUtilsTest {

    @Test
    public void isJSONValidTest() {
	String testJson = "{\"title\" : \"New Title Update\",\"description\": \"new description update\"}";
	assertTrue(JSONUtils.isJSONValid(testJson));
	testJson = "{\"title\" : \"New Title Update\",description: \"new description update\"}";
	assertFalse(JSONUtils.isJSONValid(testJson));
    }

    @Test
    public void isValidateInput() {
	String testJson = "{\"title\" : \"New Title Update\",\"description\": \"new description update\"}";
	assertTrue(JSONUtils.validateInput(testJson));
	// testJson = "{\"jnsfhshdjsjk\" : \"New Title Update\",\"description\":
	// \"new description update\"}";
	testJson = "{\"jnsfhshdjsjk\"}";
	assertFalse(JSONUtils.validateInput(testJson));
    }
}
