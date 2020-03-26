package gov.nist.oar.customizationapi.service;

import java.util.ArrayList;

import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Map.Entry;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.mongodb.MongoException;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Projections;
import com.mongodb.client.model.UpdateOptions;
import com.mongodb.client.result.DeleteResult;

import gov.nist.oar.customizationapi.config.MongoConfig;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
import gov.nist.oar.customizationapi.helpers.JSONUtils;
import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.customizationapi.repositories.EditorService;

/**
 * Implemention of EditorService interface where request to get data, get updates
 * delete changes and Update field requests are processed and corresponding fields in mongodb is updated.
 * @author Deoyani Nandrekar-Heinis
 */
@Service
public class EditorServiceImpl implements EditorService {
	private Logger logger = LoggerFactory.getLogger(EditorServiceImpl.class);

	@Autowired
	MongoConfig mconfig;
	
	@Autowired
	UserDetailsExtractor userDetailsExtractor;
	
	@Value("${nist.arkid:testid}")
	String nistarkid;

	@Override
	public Document patchRecord(String param, String recordid) throws CustomizationException, InvalidInputException {

		try {
			// Validate JSON and Validate schema against json-customization schema
			JSONUtils.validateInput(param);
			Document update = Document.parse(param);
			update.remove("_id");
			update.append("ediid", recordid);
			return this.updateChangesHelper(recordid, update);
		} catch (InvalidInputException iexp) {
			logger.error("Error while Processing input json data: " + iexp.getMessage());
			throw new InvalidInputException("Error while processing input JSON data:" + iexp.getMessage());
		}

	}

	@Override
	public Document getRecord(String recordid) throws CustomizationException {
		return this.mergeDataOnTheFly(recordid);
	}

	@Override
	public Document deleteRecordChanges(String recordid) throws CustomizationException {
		deleteRecordChangesInCache(recordid);
		
		if (!checkRecordInCache(recordid, mconfig.getRecordCollection()))
			throw new ResourceNotFoundException("Record not found in Cache.");

		return mconfig.getRecordCollection().find(Filters.eq("ediid", recordid)).first();
		 
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
	private Document updateChangesHelper(String recordid, Document update) throws CustomizationException, ResourceNotFoundException {

		if (!this.checkRecordInCache(recordid, mconfig.getChangeCollection()))
			this.putDataInCacheOnlyChanges(update, mconfig.getChangeCollection());

		else {
			updateChangesCache(recordid, update);
		}
		return mergeDataOnTheFly(recordid);

	}

	private void updateChangesCache(String recordid, Document update) {
		try {
			Date now = new Date();
			List<Document> updateDetails = new ArrayList<Document>();

			FindIterable<Document> fd = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid))
					.projection(Projections.include("_updateDetails"));
			Iterator<Document> iterator = fd.iterator();
			while (iterator.hasNext()) {
				Document d = iterator.next();
				if (d.containsKey("_updateDetails")) {
					List<?> updateHistory = (List<?>) d.get("_updateDetails");
					for (int i = 0; i < updateHistory.size(); i++)
						updateDetails.add((Document) updateHistory.get(i));

				}
			}

			AuthenticatedUserDetails authenticatedUser = userDetailsExtractor.getUserDetails();
			Document userDetails = new Document();
			userDetails.append("userId", authenticatedUser.getUserId());
			userDetails.append("userName", authenticatedUser.getUserName());
			userDetails.append("userLastName", authenticatedUser.getUserLastName());
			userDetails.append("userEmail", authenticatedUser.getUserEmail());

			Document updateInfo = new Document();
			updateInfo.append("_userDetails", userDetails);
			updateInfo.append("_updateDate", now);
			updateDetails.add(updateInfo);

			update.append("_updateDetails", updateDetails);

			if (update.containsKey("_id"))
				update.remove("_id");

			Document tempUpdateOp = new Document("$set", update);

			if (tempUpdateOp.containsKey("_id"))
				tempUpdateOp.remove("_id");

			Document doc = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first();

			for (Entry<String, Object> entry : tempUpdateOp.entrySet()) {
				if (doc.containsKey(entry.getKey())) {
					doc.replace(entry.getKey(), doc.get(entry.getKey()), entry.getValue());
				}

			}

			mconfig.getChangeCollection().updateOne(Filters.eq("ediid", recordid), tempUpdateOp,
					new UpdateOptions().upsert(true));
		} catch (MongoException ex) {
			logger.error("Error while update data in cache db" + ex.getMessage());
			throw new MongoException("Error while putting updated data in cache db." + ex.getMessage());
		}

	}

	/**
	 * It first checks whether recordid provided is of proper format and allowed to
	 * be used to search in the database. It uses find method to search database.
	 * 
	 * @param recordid
	 * @return
	 */
	public boolean checkRecordInCache(String recordid, MongoCollection<Document> mcollection) {
		try {
			Pattern p = Pattern.compile("[^a-z0-9]", Pattern.CASE_INSENSITIVE);
			Matcher m = p.matcher(recordid);
			if (m.find()) {
				logger.error("Input record id is not valid,, check input parameters.");
				throw new IllegalArgumentException("check input parameters.");
			}
			
			if(recordid.startsWith("mds"))
				recordid = "ark:/"+this.nistarkid+"/"+recordid;
			long count = mcollection.countDocuments(Filters.eq("ediid", recordid));
			return count != 0;
		} catch (MongoException e) {
			logger.error("Error finding data from MongoDB for requested record id");
			throw e;
		}
	}

	/**
	 * This function inserts updated record changes in the Mongodb changes
	 * collection.
	 * 
	 * @param update
	 * @param mcollection
	 */
	public void putDataInCacheOnlyChanges(Document update, MongoCollection<Document> mcollection) {
		try {
			update.remove("_id");
			mcollection.insertOne(update);
		} catch (MongoException ex) {
			logger.error("Error while putting changes in cache db" + ex.getMessage());
			throw new MongoException("Error while putting changes in cache db." + ex.getMessage());
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
	public Document mergeDataOnTheFly(String recordid) throws CustomizationException, ResourceNotFoundException {
		try {


			if (!checkRecordInCache(recordid, mconfig.getRecordCollection()))
				throw new ResourceNotFoundException("Record not found in Cache.");

			Document doc = mconfig.getRecordCollection().find(Filters.eq("ediid", recordid)).first();

			Document changes = null;
			if (checkRecordInCache(recordid, mconfig.getChangeCollection())) {
				changes = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first();
				if (changes.containsKey("_id"))
					changes.remove("_id");

			}

			if (changes != null) {
				for (Entry<String, Object> entry : changes.entrySet()) {
//					System.out.println("key:" + entry.getKey());
					if (doc.containsKey(entry.getKey())) {
						doc.replace(entry.getKey(), doc.get(entry.getKey()), entry.getValue());
					}else {
					
					//if(entry.getKey().equals("_updateDetails")) {
						doc.append(entry.getKey(), entry.getValue());
					//}
					}

				}
			}

			return doc;

		} catch (MongoException ex) {
			logger.error("Error while update data in cache db" + ex.getMessage());
			throw new MongoException("Error while putting updated data in cache db." + ex.getMessage());
		}

	}

	/**
	 * Find the record of given id in the collection and remove.
	 * 
	 * @param recordid    Unique record identifier
	 * @param mcollection MongoDB Collection
	 * @return true if the record is deleted successfully.
	 */
	public boolean deleteRecordChangesInCache(String recordid) throws ResourceNotFoundException {
		try {
			
			if (!checkRecordInCache(recordid, mconfig.getChangeCollection()))
				throw new ResourceNotFoundException("Record not found in Cache.");
			
			boolean deleted = false;
			Document d = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first();

			if (d != null) {
				DeleteResult result = mconfig.getChangeCollection().deleteOne(d);
				if (result.getDeletedCount() == 1)
					deleted = true;
			}

			return deleted;

		} catch (MongoException ex) {
			logger.error("Error deleting data in cache db" + ex.getMessage());
			throw new MongoException("Error while deleteing data in cache db." + ex.getMessage());
		}

	}
}
