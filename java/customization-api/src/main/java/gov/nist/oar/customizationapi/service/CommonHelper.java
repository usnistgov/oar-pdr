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
import java.util.Map.Entry;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mongodb.MongoException;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.result.DeleteResult;

import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.helpers.JSONUtils;

/**
 * Validate input parameters to check if its valid json and passes schema test.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class CommonHelper {
	private Logger logger = LoggerFactory.getLogger(CommonHelper.class);

	/**
	 * Added this functionality to process input json string
	 * 
	 * @param json
	 * @return
	 * @throws IOException
	 * @throws InvalidInputException
	 */
	public boolean validateInputParams(String json) throws IOException, InvalidInputException {
		logger.info("CommonHelper Validating input parameteres in the ProcessInputRequest class.");
		// validate JSON and Validate schema against json-customization schema
		return JSONUtils.validateInput(json);

	}

	/***
	 * Check whether original record is put in the cache if not throw exception
	 * 
	 * @param recordid
	 */
	public void checkRecordInCache(String recordid, MongoCollection<Document> mcollection) {
		logger.info("CommonHelper Check if record exists in cache requested by :"+recordid );
		if (!isRecordInCache(recordid, mcollection))
			throw new ResourceNotFoundException("Record not found in Cache.");
	}

	/***
	 * Retrieve record from cache.
	 * 
	 * @param recordid
	 * @return
	 */
	public Document getRecordFromCache(String recordid, MongoCollection<Document> mcollection) {
		
		logger.info("CommonHelper Retrieve the record requested by "+recordid);
		return mcollection.find(Filters.eq("ediid", recordid)).first();
	}

	/**
	 * Record Identifier Helper
	 */
	public String getIdentifier(String requestedID, String nistarkid) {

		logger.info("CommonHelper get the identifier if there is ");
		if (requestedID.startsWith("mds"))
			requestedID = "ark:/" + nistarkid + "/" + requestedID;
		return requestedID;
	}

	/**
	 * It first checks whether recordid provided is of proper format and allowed to
	 * be used to search in the database. It uses find method to search database.
	 * 
	 * @param recordid
	 * @return
	 */
	public boolean isRecordInCache(String recordid, MongoCollection<Document> mcollection) {
		try {
			Pattern p = Pattern.compile("[^a-z0-9_./:-]", Pattern.CASE_INSENSITIVE);
			Matcher m = p.matcher(recordid);
			if (m.find()) {
				logger.error("Input record id is not valid,, check input parameters.");
				throw new IllegalArgumentException("check input parameters.");
			}

//			if (recordid.startsWith("mds"))
//				recordid = "ark:/" + this.nistarkid + "/" + recordid;
			long count = mcollection.countDocuments(Filters.eq("ediid", recordid));
			return count != 0;
		} catch (MongoException e) {
			logger.error("Error finding data from MongoDB for requested record id");
			throw e;
		}
	}

	/**
	 * Find the record of given id in the collection and remove.
	 * 
	 * @param recordid    Unique record identifier
	 * @param mcollection MongoDB Collection
	 * @return true if the record is deleted successfully.
	 */
	public boolean deleteRecordInCache(String recordid, MongoCollection<Document> mcollection)
			throws ResourceNotFoundException {
		try {
			
			boolean deleted = false;
			Document d = mcollection.find(Filters.eq("ediid", recordid)).first();

			if (d != null) {
				DeleteResult result = mcollection.deleteMany(d);
				if (result.getDeletedCount() >= 1)
					deleted = true;
			}

			return deleted;

		} catch (MongoException ex) {
			logger.error("Error deleting data in cache db" + ex.getMessage());
			throw new MongoException("Error while deleteing data in cache db." + ex.getMessage());
		}

	}

	/**
	 * To update the record in the cached database
	 * 
	 * @param recordid an ediid of the record
	 * @param update   json to update
	 * @return Return true if data is updated successfully.
	 * @throws CustomizationException
	 */
	public Document mergeDataOnTheFly(String recordid, MongoCollection<Document> originalcollection,
			MongoCollection<Document> changescollection) throws CustomizationException, ResourceNotFoundException {
		try {

			Document doc = this.getRecordFromCache(recordid, originalcollection);

			Document changes = null;
			try {
				if (isRecordInCache(recordid, changescollection)) {
					changes = changescollection.find(Filters.eq("ediid", recordid)).first();
					if (changes.containsKey("_id"))
						changes.remove("_id");

				}
			} catch (Exception e) {
				logger.info("There are issues gettinf data from changes collection.");

			}

			if (changes != null) {
				for (Entry<String, Object> entry : changes.entrySet()) {

					if (doc.containsKey(entry.getKey()))
						doc.replace(entry.getKey(), doc.get(entry.getKey()), entry.getValue());
					else
						doc.append(entry.getKey(), entry.getValue());

				}
			}

			return doc;

		} catch (MongoException ex) {
			logger.error("Error while update data in cache db" + ex.getMessage());
			throw new MongoException("Error while putting updated data in cache db." + ex.getMessage());
		}

	}
}
