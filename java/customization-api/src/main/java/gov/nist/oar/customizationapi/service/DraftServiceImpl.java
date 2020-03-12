package gov.nist.oar.customizationapi.service;

import java.util.Map.Entry;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.mongodb.MongoException;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.result.DeleteResult;

import gov.nist.oar.customizationapi.config.MongoConfig;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
//import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.customizationapi.repositories.DraftService;

@Service
public class DraftServiceImpl implements DraftService {

	private Logger logger = LoggerFactory.getLogger(DraftServiceImpl.class);

	@Autowired
	MongoConfig mconfig;

//	@Autowired
//	UserDetailsExtractor userDetailsExtractor;

	@Override
	public Document getDraft(String recordid, String view) throws CustomizationException {
		logger.info("Return the draft saved in the cache database.");
		return returnMergedChanges(recordid, view);
	}

	@Override
	public void putDraft(String recordid, Document record) throws CustomizationException, InvalidInputException {
		logger.info("Put the nerdm record in the data cache.");
		// return updateDataInCache(recordid, record);
		try {
			mconfig.getRecordCollection().insertOne(record);
		} catch (MongoException exp) {
			logger.error("Error while putting updated data in records db" + exp.getMessage());
			throw new CustomizationException("Error updating records (database)" + exp.getMessage());
		}
	}

	@Override
	public boolean deleteDraft(String recordid) throws CustomizationException {
		logger.info("Delete the record and changes from the database.");

		return deleteRecordInCache(recordid, mconfig.getRecordCollection())
				&& deleteRecordInCache(recordid, mconfig.getChangeCollection());

	}

	/**
	 * #############$%$$$^^^^^^^^^ This method returns the nerdm record with changes
	 * merged on the fly.
	 * 
	 * @param recordid
	 * @param view
	 * @return
	 */
	public Document returnMergedChanges(String recordid, String view) throws CustomizationException {
		try {
			if (view.equalsIgnoreCase("updates"))
				return mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first();

			return mergeDataOnTheFly(recordid);
			//return mconfig.getRecordCollection().find(Filters.eq("ediid", recordid)).first();
		} catch (MongoException exp) {
			logger.error("Error while putting updated data in records db" + exp.getMessage());
			throw new CustomizationException("Error updating records (database)" + exp.getMessage());

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
	public Document mergeDataOnTheFly(String recordid) throws CustomizationException {
		try {

			if (!checkRecordInCache(recordid, mconfig.getRecordCollection()))
				throw new CustomizationException("Record not found in Cache.");

			Document doc = mconfig.getRecordCollection().find(Filters.eq("ediid", recordid)).first();

			Document tempUpdateOp = null;
			if (checkRecordInCache(recordid, mconfig.getChangeCollection())) {
				tempUpdateOp = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first();
				if (tempUpdateOp.containsKey("_id"))
					tempUpdateOp.remove("_id");

			}

			if (tempUpdateOp != null) {
				for (Entry<String, Object> entry : tempUpdateOp.entrySet()) {
					System.out.println("key:" + entry.getKey());
					if (doc.containsKey(entry.getKey())) {
						doc.replace(entry.getKey(), doc.get(entry.getKey()), entry.getValue());
					}
					if(entry.getKey().equals("_updateDetails")) {
						doc.append(entry.getKey(), entry.getValue());
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
	 * It first checks whether recordid provided is of proper format and allowed to
	 * be used to search in the database. It uses find method to search database.
	 * 
	 * @param recordid
	 * @returns
	 */
	public boolean checkRecordInCache(String recordid, MongoCollection<Document> mcollection) {
		try {
			Pattern p = Pattern.compile("[^a-z0-9]", Pattern.CASE_INSENSITIVE);
			Matcher m = p.matcher(recordid);
			if (m.find()) {
				logger.error("Input record id is not valid,, check input parameters.");
				throw new IllegalArgumentException("check input parameters.");
			}
			long count = mcollection.countDocuments(Filters.eq("ediid", recordid));
			return count != 0;
		} catch (MongoException e) {
			logger.error("Error finding data from MongoDB for requested record id");
			throw e;
		}
	}

//	/**
//	 * To update the record in the cached database
//	 * 
//	 * @param recordid an ediid of the record
//	 * @param update   json to update
//	 * @return Return true if data is updated successfully.
//	 */
//	public boolean updateDataInCache(String recordid,  Document update) {
//		try {
//			Date now = new Date();
//			List<Document> updateDetails = new ArrayList<Document>();
//
//			FindIterable<Document> fd = mconfig.getRecordCollection().find(Filters.eq("ediid", recordid))
//					.projection(Projections.include("_updateDetails"));
//			Iterator<Document> iterator = fd.iterator();
//			while (iterator.hasNext()) {
//				Document d = iterator.next();
//				if (d.containsKey("_updateDetails")) {
//					List<?> updateHistory = (List<?>) d.get("_updateDetails");
//					for (int i = 0; i < updateHistory.size(); i++)
//						updateDetails.add((Document) updateHistory.get(i));
//
//				}
//			}
//
//			AuthenticatedUserDetails authenticatedUser = userDetailsExtractor.getUserDetails();
//			Document userDetails = new Document();
//			userDetails.append("userId", authenticatedUser.getUserId());
//			userDetails.append("userName", authenticatedUser.getUserName());
//			userDetails.append("userLastName", authenticatedUser.getUserLastName());
//			userDetails.append("userEmail", authenticatedUser.getUserEmail());
//
//			Document updateInfo = new Document();
//			updateInfo.append("_userDetails", userDetails);
//			updateInfo.append("_updateDate", now);
//			updateDetails.add(updateInfo);
//
//			update.append("_updateDetails", updateDetails);
//
//			if (update.containsKey("_id"))
//				update.remove("_id");
//
//			Document tempUpdateOp = new Document("$set", update);
//
//			if (tempUpdateOp.containsKey("_id"))
//				tempUpdateOp.remove("_id");
//
//			mconfig.getRecordCollection().updateOne(Filters.eq("ediid", recordid), tempUpdateOp, new UpdateOptions().upsert(true));
//
//			return true;
//		} catch (MongoException ex) {
//			logger.error("Error while update data in cache db" + ex.getMessage());
//			throw new MongoException("Error while putting updated data in cache db." + ex.getMessage());
//		}
//
//	}

	/**
	 * Find the record of given id in the collection and remove.
	 * 
	 * @param recordid    Unique record identifier
	 * @param mcollection MongoDB Collection
	 * @return true if the record is deleted successfully.
	 */
	public boolean deleteRecordInCache(String recordid, MongoCollection<Document> mcollection) {
		try {
			boolean deleted = false;
			Document d = mcollection.find(Filters.eq("ediid", recordid)).first();

			if (d != null) {
				DeleteResult result = mcollection.deleteOne(d);
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
