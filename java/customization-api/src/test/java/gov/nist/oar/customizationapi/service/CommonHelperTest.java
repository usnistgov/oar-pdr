package gov.nist.oar.customizationapi.service;

import java.io.IOException;

import org.junit.Test;

import gov.nist.oar.customizationapi.exceptions.InvalidInputException;

/**
 * Test ProcessInputRequest class to check whether input json is valid
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class CommonHelperTest {

	@Test
	public void validateInputParamsTest() throws IOException, InvalidInputException {
		CommonHelper processInputRequest = new CommonHelper();
		String json = "{\n" + 
				"    \"title\" : \"Title of Record\",\n" + 
				"    \"description\" : [\"Description for the record\"],\n" + 
				"    \"ediid\" : \"FDB5909746815200E043065706813E54137\"\n" + 
				"}";
		
		org.junit.Assert.assertTrue(processInputRequest.validateInputParams(json));
		
	}
}
