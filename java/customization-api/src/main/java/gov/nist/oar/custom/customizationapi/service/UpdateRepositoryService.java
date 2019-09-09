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

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.mongodb.MongoException;

import gov.nist.oar.custom.customizationapi.config.MongoConfig;
import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.custom.customizationapi.helpers.JSONUtils;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;

/**
 * UpdateRepository is the service class which takes input from client to edit
 * or update records in cache database. The functions are written to process
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Service
public class UpdateRepositoryService implements UpdateRepository {

    private Logger logger = LoggerFactory.getLogger(UpdateRepositoryService.class);

    @Autowired
    MongoConfig mconfig;

    @Autowired
    DatabaseOperations accessData;

    /**
     * Update record in backend database with changes provided in the form of JSON
     * input. Backend database is for caching changes before publishing it to
     * backend metadata server.
     * 
     * @throws CustomizationException
     * @throws InvalidInputException
     * @throws ResourceNotFoundException
     */
    @Override
    public Document update(String params, String recordid)
	    throws InvalidInputException, ResourceNotFoundException, CustomizationException {
	logger.info("Update: operation to save draft called.");
	processInputHelper(params, recordid);
	return accessData.getData(recordid, mconfig.getRecordCollection());
    }

    /**
     * Check the inputed values which are of JSON format, check if JSON is valid and
     * passes the schema. Valid input is processed and patched in the backed
     * database.
     * 
     * @param params
     * @param recordid
     * @return bolean
     * @throws InvalidInputException
     */
    private boolean processInputHelper(String params, String recordid) throws InvalidInputException {
	try {

	    // Validate JSON and Validate schema against json-customization schema
	    JSONUtils.validateInput(params);

	    // this.accessData.checkRecordInCache(recordid, recordCollection);
	    Document update = Document.parse(params);
	    update.remove("_id");
	    update.append("ediid", recordid);
	    return this.updateHelper(recordid, update);

	} catch (InvalidInputException iexp) {
	    logger.error("Error while Processing input json data: " + iexp.getMessage());
	    throw new InvalidInputException("Error while processing input JSON data:" + iexp.getMessage());

	}

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
	logger.info("get data operation in service called.");
	return accessData.getData(recordid, mconfig.getRecordCollection());
    }

    /**
     * Save action can accept changes and save them or just return the updated data
     * from cache.
     * 
     * @throws InvalidInputException
     * @throws CustomizationException
     */
    @Override
    public Document save(String recordid, String params) throws InvalidInputException, CustomizationException {

	logger.info("save and send finalized draft to backend service.");
	Document update = null;
	try {

	    if (JSONUtils.isJSONValid(params) && !(params.isEmpty() || params == null)) {
		// If input is not empty process it first.
		processInputHelper(params, recordid);
	    }

	    // if record exists
	    if (accessData.checkRecordInCache(recordid, mconfig.getChangeCollection())) {
		// send data to mdserver

		RestTemplate restTemplate = new RestTemplate();
		Document d = accessData.getData(recordid, mconfig.getChangeCollection());
		HttpHeaders headers = new HttpHeaders();
		HttpEntity<Document> requestUpdate = new HttpEntity<>(d, headers);
		update = (Document) restTemplate.patchForObject(mconfig.getMetadataServer(), requestUpdate,
			Document.class);
	    }

	    // on successful return delete record from DB
	    if (update != null && update.size() != 0) {
		accessData.deleteRecordInCache(recordid, mconfig.getChangeCollection());
		accessData.deleteRecordInCache(recordid, mconfig.getRecordCollection());

		return update;

	    } else {
		throw new CustomizationException("The data can not be updated successfully in the backend server.");
	    }
	} catch (InvalidInputException ex) {

	    logger.error("Error while finalizing changes.InvalidInputException:" + ex.getMessage());
	    throw new InvalidInputException("Error while finalizing changes. " + ex.getMessage());

	} catch (MongoException ex) {
	    logger.error("There is an error in save operation while accessing/updating data from backend database."
		    + ex.getMessage());
	    throw new CustomizationException("There is an error accessing/updating data from backend database.");

	}

    }

    @Override
    public boolean delete(String recordid) throws CustomizationException {

	logger.info("delete operation in service called.");
	return accessData.deleteRecordInCache(recordid, mconfig.getRecordCollection())
		&& accessData.deleteRecordInCache(recordid, mconfig.getChangeCollection());
    }

}
