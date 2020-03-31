package gov.nist.oar.customizationapi.service;

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
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.result.DeleteResult;

import gov.nist.oar.customizationapi.config.MongoConfig;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
//import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.customizationapi.repositories.DraftService;
/**
 * Implementation of DraftService interface where request to put draft in the database, get the draft,
 * delete once editing completed.
 * @author Deoyani Nandrekar-Heinis
 */
@Service
public class DraftServiceImpl implements DraftService {

	private Logger logger = LoggerFactory.getLogger(DraftServiceImpl.class);

	@Autowired
	MongoConfig mconfig;

	@Value("${nist.arkid:testid}")
	String nistarkid;

	/**
	 * Service returns metadata associated with requested record, if there are changes made from user/client service 
	 * the returned metadata returns updated record/metadata
	 */
	@Override
	public Document getDraft(String recordid, String view) throws CustomizationException, ResourceNotFoundException, InvalidInputException {
		logger.info("Return the draft saved in the cache database.");
		return returnMergedChanges(recordid, view);
	}

	/**
	 * Create new record or enter metadata entry in the database for requested ID.
	 */
	@Override
	public void putDraft(String recordid, Document record) throws CustomizationException, InvalidInputException {
		logger.info("Put the nerdm record in the data cache.");

		try {
			if (checkRecordInCache(recordid, mconfig.getRecordCollection()))
				deleteRecordInCache(recordid, mconfig.getRecordCollection());
			mconfig.getRecordCollection().insertOne(record);
		} catch (MongoException exp) {
			logger.error("Error while putting updated data in records db" + exp.getMessage());
			throw new CustomizationException("Error updating records (database)" + exp.getMessage());
		}
	}

	/**
	 * Delete metadata from the database for requested record id. 
	 * This deletes both original record and changes made by client/user application. 
	 */
	@Override
	public boolean deleteDraft(String recordid) throws CustomizationException {
		logger.info("Delete the record and changes from the database.");

		return deleteRecordInCache(recordid, mconfig.getRecordCollection())
				&& deleteRecordInCache(recordid, mconfig.getChangeCollection());

	}

	/**
	 * This method returns the nerdm record with changes
	 * merged on the fly.
	 * 
	 * @param recordid
	 * @param view
	 * @return
	 * @throws InvalidInputException 
	 */
	public Document returnMergedChanges(String recordid, String view) throws CustomizationException, ResourceNotFoundException, InvalidInputException {
		try {
			Document doc = null;
			if (view.equalsIgnoreCase("updates")){
				
				if (!checkRecordInCache(recordid, mconfig.getRecordCollection()))
					throw new ResourceNotFoundException("Record not found in Cache.");
				doc = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first() ;
				return (doc != null) ?doc: new Document();
			}
				return mergeDataOnTheFly(recordid);
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
	 * @throws InvalidInputException 
	 */
	public Document mergeDataOnTheFly(String recordid) throws CustomizationException, ResourceNotFoundException, InvalidInputException {
		try {

			if (!checkRecordInCache(recordid, mconfig.getRecordCollection()))
				throw new ResourceNotFoundException("Record not found in Cache.");

			Document doc = this.getRecordFromCache(recordid);

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
					}else
						doc.append(entry.getKey(), entry.getValue()); //any new metadata added
				}
			}

			return doc;

		} catch (MongoException ex) {
			logger.error("Error while update data in cache db" + ex.getMessage());
			throw new MongoException("Error while putting updated data in cache db." + ex.getMessage());
		}

	}
	
	public Document getRecordFromCache(String recordid) {
		if(recordid.startsWith("mds"))
			recordid = "ark:/"+this.nistarkid+"/"+recordid;
		return mconfig.getRecordCollection().find(Filters.eq("ediid", recordid)).first();
	}

	/**
	 * It first checks whether recordID provided is of proper format and allowed to
	 * be used to search in the database. It uses find method to search database.
	 * 
	 * @param recordid
	 * @throws InvalidInputException 
	 * @returns
	 */
	public boolean checkRecordInCache(String recordid, MongoCollection<Document> mcollection) throws InvalidInputException {
		try {
			Pattern p = Pattern.compile("[^a-z0-9_.-]", Pattern.CASE_INSENSITIVE);
			Matcher m = p.matcher(recordid);
			if (m.find()) {
				logger.error("Requested record id is not valid, record id has unsupported characters.");
				throw new InvalidInputException("Check the requested record id.");
			}
			if(recordid.startsWith("mds"))
				recordid = "ark:/"+this.nistarkid+"/"+recordid;   // this is added for new record ID style
			long count = mcollection.countDocuments(Filters.eq("ediid", recordid));
			return count != 0;
		} 
		catch (MongoException e) {
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
