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

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.mongodb.MongoException;

import gov.nist.oar.customizationapi.config.MongoConfig;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.helpers.JSONUtils;
import gov.nist.oar.customizationapi.repositories.UpdateRepository;

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
	public Document updateRecord(String params, String recordid)
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
	 * @return boolean
	 * @throws InvalidInputException
	 * @throws CustomizationException
	 */
	private boolean processInputHelper(String params, String recordid)
			throws InvalidInputException, CustomizationException {
		try {
			// Validate JSON and Validate schema against json-customization schema
			JSONUtils.validateInput(params);
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
	 * UpdateHelper takes input recordid and JSON input, this function checks if the
	 * record is there in cache If not it pulls record and puts in cache and then
	 * update the changes.
	 * 
	 * @param recordid
	 * @param update
	 * @return boolean
	 * @throws CustomizationException
	 */
	private boolean updateHelper(String recordid, Document update) throws CustomizationException {

		if (!this.accessData.checkRecordInCache(recordid, mconfig.getRecordCollection()))
			this.accessData.putDataInCache(recordid, mconfig.getRecordCollection());

		if (!this.accessData.checkRecordInCache(recordid, mconfig.getChangeCollection()))
			this.accessData.putDataInCacheOnlyChanges(update, mconfig.getChangeCollection());

		return accessData.updateDataInCache(recordid, mconfig.getRecordCollection(), update)
				&& accessData.updateDataInCache(recordid, mconfig.getChangeCollection(), update);
	}

	/**
	 * @param recordid
	 * @return Document
	 * @throws CustomizationException Accessing records to edit in the front end.
	 */
	@Override
	public Document getRecord(String recordid) throws CustomizationException {
		logger.info("get data operation in service called.");
		return accessData.getData(recordid, mconfig.getRecordCollection());
	}

	
	/**
	 * @param recordid
	 * @return Document
	 * @throws CustomizationException Accessing records to edit in the front end.
	 */
	@Override
	public Document getData(String recordid,String view) throws CustomizationException {
		logger.info("get data operation in service called.");
		if(view.equalsIgnoreCase("updates"))
			return accessData.getData(recordid, mconfig.getChangeCollection());
		return accessData.getData(recordid, mconfig.getRecordCollection());
	}

//	/**
//	 * Save action can accept changes and save them or just return the updated data
//	 * from cache.
//	 * 
//	 * @param params, recordid
//	 * @return Document
//	 * @throws InvalidInputException
//	 * @throws CustomizationException
//	 */
//	@Override
//	public Document save(String recordid, String params) throws InvalidInputException, CustomizationException {
//		logger.info("save and send finalized draft to backend service.");
//		Document update = null;
//		try {
//			if (!(params.isEmpty() || params == null)) {
//				// If input is not empty process it first.
//				processInputHelper(params, recordid);
//			}
//			// if record exists send changes to mdserver
//			if (accessData.checkRecordInCache(recordid, mconfig.getChangeCollection())) {
//				// Document d = accessData.getData(recordid, mconfig.getChangeCollection());
//				BackendServerOperations bkOperations = new BackendServerOperations(mconfig.getMetadataServer(),
//						mconfig.getMDSecret());
//				update = bkOperations.sendChangesToServer(recordid,
//						accessData.getData(recordid, mconfig.getChangeCollection()));
//
//			}
//			// on successful return delete record from DB
//			if (update != null && update.size() != 0) {
//				// this.delete(recordid);
//				return update;
//			} else {
//				throw new CustomizationException("The data can not be updated successfully in the backend server.");
//			}
//		} catch (InvalidInputException ex) {
//			logger.error("Error while finalizing changes.InvalidInputException:" + ex.getMessage());
//			throw new InvalidInputException("Error while finalizing changes. " + ex.getMessage());
//		} catch (MongoException ex) {
//			logger.error("There is an error in save operation while accessing/updating data from backend database."
//					+ ex.getMessage());
//			throw new CustomizationException("There is an error accessing/updating data from backend database.");
//		}
//
//	}

	/**
	 * @param recordid
	 * @return boolean
	 * @throws CustomizationException
	 */
	@Override
	public boolean delete(String recordid) throws CustomizationException {

		logger.info("delete operation in service called.");
		return accessData.deleteRecordInCache(recordid, mconfig.getRecordCollection())
				&& accessData.deleteRecordInCache(recordid, mconfig.getChangeCollection());
	}
	
	/**
	 * Save action can accept changes and save them or just return the updated data
	 * from cache.
	 * 
	 * @param params, recordid
	 * @return Document
	 * @throws InvalidInputException
	 * @throws CustomizationException
	 */
	@Override
	public boolean put(String recordid, String params) throws InvalidInputException, CustomizationException {
		logger.info("save and send finalized draft to backend service.");

		try {
			if (!(params.isEmpty() || params == null)) {
				// If input is not empty process it first.
				return inputDocumentHelper(params, recordid);
			}
			throw new InvalidInputException("Input is null or JSON is not valid.");

		} catch (InvalidInputException ex) {
			logger.error("Error while finalizing changes.InvalidInputException:" + ex.getMessage());
			throw new InvalidInputException("Error while finalizing changes. " + ex.getMessage());
		} catch (MongoException ex) {
			logger.error("There is an error in save operation while accessing/updating data from backend database."
					+ ex.getMessage());
			throw new CustomizationException("There is an error accessing/updating data from backend database.");
		}

	}

	/**
	 * Check the inputed values which are of JSON format, check if JSON is valid and
	 * passes the schema. Valid input is processed and patched in the backed
	 * database.
	 * 
	 * @param params
	 * @param recordid
	 * @return boolean
	 * @throws InvalidInputException
	 * @throws CustomizationException
	 */
	private boolean inputDocumentHelper(String params, String recordid)
			throws InvalidInputException, CustomizationException {
		try {
			// Validate JSON and Validate schema against json-customization schema
			JSONUtils.validateInput(params);
			Document update = Document.parse(params);
			update.remove("_id");
			update.append("ediid", recordid);

			if (!this.accessData.checkRecordInCache(recordid, mconfig.getRecordCollection())) {
				this.accessData.putDataInCache(recordid, mconfig.getRecordCollection());
				return true;
			} else
				return false;

		} catch (InvalidInputException iexp) {
			logger.error("Error while Processing input json data: " + iexp.getMessage());
			throw new InvalidInputException("Error while processing input JSON data:" + iexp.getMessage());
		}
	}

}
