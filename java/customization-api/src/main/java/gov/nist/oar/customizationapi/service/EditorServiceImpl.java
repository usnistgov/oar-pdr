package gov.nist.oar.customizationapi.service;

import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Map.Entry;

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

import gov.nist.oar.customizationapi.config.MongoConfig;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
import gov.nist.oar.customizationapi.helpers.JSONUtils;
import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.customizationapi.repositories.EditorService;

/**
 * Implemention of EditorService interface where request to get data, get
 * updates delete changes and Update field requests are processed and
 * corresponding fields in mongodb is updated.
 * 
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

	CommonHelper commonHelper = new CommonHelper();

	@Override
	public Document getRecord(String recordid) throws CustomizationException {
		logger.info("Retrieve the metadata record from chache requested by ::"+recordid);
		recordid = commonHelper.getIdentifier(recordid, nistarkid);
		commonHelper.checkRecordInCache(recordid, mconfig.getRecordCollection());
		return commonHelper.mergeDataOnTheFly(recordid,mconfig.getRecordCollection(), mconfig.getChangeCollection());
	}

	@Override
	public Document patchRecord(String param, String recordid) throws CustomizationException, InvalidInputException {
		logger.info("Updated changes in cache made by client and reuested by :: "+recordid);

		try {
			recordid = commonHelper.getIdentifier(recordid, nistarkid);
			commonHelper.checkRecordInCache(recordid, mconfig.getRecordCollection());
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

	/***
	 * Delete only the changes  and return original record
	 */
	@Override
	public Document deleteRecordChanges(String recordid) throws CustomizationException {
		logger.info("Delete only the changes in record from cache requested by ::"+recordid);
		recordid = commonHelper.getIdentifier(recordid, nistarkid);
		commonHelper.checkRecordInCache(recordid, mconfig.getRecordCollection());
		commonHelper.deleteRecordInCache(recordid, mconfig.getChangeCollection());
		return commonHelper.getRecordFromCache(recordid, mconfig.getRecordCollection());
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
	private Document updateChangesHelper(String recordid, Document update)
			throws CustomizationException, ResourceNotFoundException {

		if (!commonHelper.isRecordInCache(recordid, mconfig.getChangeCollection()))
			this.putDataInCacheOnlyChanges(update, mconfig.getChangeCollection());

		else
			updateChangesCache(recordid, update);

		return commonHelper.mergeDataOnTheFly(recordid,mconfig.getRecordCollection(), mconfig.getChangeCollection());

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

}
