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
package gov.nist.oar.customizationapi.repositories;

import org.bson.Document;

import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;

/**
 * This is repository is defined to get input json for the record in mongodb, 
 * update cache or save final results by passing it to backend service.
 * @author Deoyani Nandrekar-Heinis
 *
 */
public interface UpdateRepository {
    /**
     * Updates record with provided input data
     * @param param  JSON string 	
     * @param recordid string ediid/unique record id
     * @return	Complete record with updated fields
     * @throws CustomizationException if there is an issue update record in data base
     * 				      or getting record from backend for the first time to put chnages in cache, it would throw internal service error
     * @throws InvalidInputException If input parameters are not valid and fail JSON validation tests, this exception is thrown
     */
    public Document update(String param, String recordid)  throws CustomizationException, InvalidInputException;
    
    /**
     * Returns the complete record in JSON format which can be used to edit
     * @param recordid string ediid/unique record id 
     * @return Document a complete JSON data
     * @throws CustomizationException Throws exception if there is issue while accessing data 
     */
    public Document edit(String recordid) throws CustomizationException;
    /**
     * Returns the document once save data
     * @param recordid string ediid/unique record id
     * @param params JSON string input or empty 
     * @return Complete document in JSON format
     * @throws CustomizationException if there is an issue update record in data base
     * 				      or getting record from backend for the first time to put chnages in cache, it would throw internal service error
     * @throws InvalidInputException If input parameters are not valid and fail JSON validation tests, this exception is thrown
     */
    public Document save(String recordid, String params) throws CustomizationException, InvalidInputException;
    /**
     * Delete record from the database
     * @param recordid string ediid/unique record id
     * @return boolean 
     * @throws CustomizationException Exception thrown if any error is thrown while deleting record from backend
     */
    public boolean delete(String recordid) throws CustomizationException;
}
