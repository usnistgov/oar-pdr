package gov.nist.oar.customizationapi.repositories;

import org.bson.Document;

import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;

public interface DraftService {
	
	/**
	 * Returns the complete record in JSON format which can be used to edit
	 * 
	 * @param recordid string ediid/unique record id
	 * @return Document a complete JSON data
	 * @throws CustomizationException Throws exception if there is issue while
	 *                                accessing data
	 */
	public Document getDraft(String recordid,String view) throws CustomizationException;
	
	/**
	 * Returns the document once save data
	 * 
	 * @param recordid string ediid/unique record id
	 * @param params   JSON string input or empty
	 * @return Complete document in JSON format
	 * @throws CustomizationException if there is an issue update record in data
	 *                                base or getting record from backend for the
	 *                                first time to put chnages in cache, it would
	 *                                throw internal service error
	 * @throws InvalidInputException  If input parameters are not valid and fail
	 *                                JSON validation tests, this exception is
	 *                                thrown
	 */
	public void putDraft(String recordid, Document params) throws CustomizationException, InvalidInputException;
	
	/**
	 * Delete record from the database
	 * 
	 * @param recordid string ediid/unique record id
	 * @return boolean
	 * @throws CustomizationException Exception thrown if any error is thrown while
	 *                                deleting record from backend
	 */
	public boolean deleteDraft(String recordid) throws CustomizationException;
	


}
