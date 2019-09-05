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

import java.io.IOException;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.mongodb.client.MongoCollection;

import gov.nist.oar.custom.customizationapi.config.MongoConfig;
import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.custom.customizationapi.helpers.JSONUtils;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;

/**
 * UpdateRepository is the service class which takes input from client to edit
 * or update records in cache database. The funtions are written to process
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Service
public class UpdateRepositoryService implements UpdateRepository {

    private Logger logger = LoggerFactory.getLogger(UpdateRepositoryService.class);

    @Autowired
    MongoConfig mconfig;

    @Autowired
    DataOperations accessData;

    /**
     * Update record in backend database with changes provided in the form of JSON input.
     * Backend database is for caching changes before publishing it to backend metadata server.
     * 
     * @throws CustomizationException
     * @throws InvalidInputException
     * @throws ResourceNotFoundException
     */
    @Override
    public Document update(String params, String recordid) throws InvalidInputException, ResourceNotFoundException,
    CustomizationException{
	
	processInputHelper(params, recordid);
	return accessData.getData(recordid, mconfig.getRecordCollection());
	
    }

    /**
     * Check the inputed values which are of JSON format, check if JSON is valid and passes the schema.
     * Valid input is processed and patched in the backed database.
     * @param params
     * @param recordid
     * @return bolean
     * @throws InvalidInputException
     */
    private boolean processInputHelper(String params, String recordid) throws InvalidInputException {
//	ProcessInputRequest req = new ProcessInputRequest();
//	if (req.validateInputParams(params)) {
	// validate json

	JSONUtils.isJSONValid(params);
	// Validate schema against json-customization schema
	if (JSONUtils.validateInput(params)) {

	    // this.accessData.checkRecordInCache(recordid, recordCollection);
	    Document update = Document.parse(params);
	    update.remove("_id");
	    update.append("ediid", recordid);
	    return this.updateHelper(recordid, update);
	} else
	    return false;

	// return accessData.updateDataInCache(recordid, recordCollection,
	// update);

    }

    /**
     * UpdateHelper takes input recordid and json input, this function checks if the
     * record is there in cache If not it pulls record and puts in cache and then
     * update the changes.
     * 
     * @param recordid
     * @param update
     * @return
     */
    private boolean updateHelper(String recordid, Document update) {


	if (!this.accessData.checkRecordInCache(recordid, mconfig.getRecordCollection()))
	    this.accessData.putDataInCache(recordid, mconfig.getRecordCollection());

	if (!this.accessData.checkRecordInCache(recordid, mconfig.getChangeCollection()))
	    this.accessData.putDataInCacheOnlyChanges(update, mconfig.getChangeCollection());

	return accessData.updateDataInCache(recordid, mconfig.getRecordCollection(), update)
		&& accessData.updateDataInCache(recordid, mconfig.getChangeCollection(), update);
    }

    /**
     * accessing records to edit in the front end.
     */
    @Override
    public Document edit(String recordid) throws CustomizationException {
	return accessData.getData(recordid, mconfig.getRecordCollection());
    }

    /**
     * Save action can accept changes and save them or just return the updated data
     * from cache.
     * 
     * @throws InvalidInputException
     */
    @Override
    public Document save(String recordid, String params) throws InvalidInputException {

	if (!(params.isEmpty() || params == null) && !processInputHelper(params, recordid))
	    return null;
//	accessData.deleteRecordInCache(recordid, mconfig.getChangeCollection());
	return accessData.getUpdatedData(recordid, mconfig.getChangeCollection());

    }

    @Override
    public boolean delete(String recordid) throws CustomizationException {

	return accessData.deleteRecordInCache(recordid, mconfig.getRecordCollection())
		&& accessData.deleteRecordInCache(recordid, mconfig.getChangeCollection());
    }

}
