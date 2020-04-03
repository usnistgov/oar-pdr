package gov.nist.oar.customizationapi.service;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.mongodb.MongoException;
import com.mongodb.client.model.Filters;

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

	CommonHelper commonHelper = new CommonHelper();
	/**
	 * Service returns metadata associated with requested record, if there are changes made from user/client service 
	 * the returned metadata returns updated record/metadata
	 */
	@Override
	public Document getDraft(String recordid, String view) throws CustomizationException, ResourceNotFoundException, InvalidInputException {
		logger.info("Return the draft saved in the cache database.");
		recordid = commonHelper.getIdentifier(recordid, nistarkid);
		commonHelper.checkRecordInCache(recordid, mconfig.getRecordCollection());
		return returnMergedChanges(recordid, view);
	}

	/**
	 * Create new record or enter metadata entry in the database for requested ID.
	 */
	@Override
	public void putDraft(String recordid, Document record) throws CustomizationException, InvalidInputException {
		logger.info("Put the nerdm record in the data cache.");
		recordid = commonHelper.getIdentifier(recordid, nistarkid);
		try {
			//If record already exists just remove and replace.
			if (commonHelper.isRecordInCache(recordid, mconfig.getRecordCollection()))
				commonHelper.deleteRecordInCache(recordid, mconfig.getRecordCollection());
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
		boolean deleted = false;
		logger.info("Delete the record and changes from the database.");
		recordid = commonHelper.getIdentifier(recordid, nistarkid);
		if(commonHelper.isRecordInCache(recordid, mconfig.getRecordCollection())) {
			commonHelper.deleteRecordInCache(recordid, mconfig.getRecordCollection());
			if(commonHelper.isRecordInCache(recordid, mconfig.getChangeCollection()))
				commonHelper.deleteRecordInCache(recordid, mconfig.getChangeCollection());
			deleted = true;
		}
		return deleted;	

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
				
				if (!commonHelper.isRecordInCache(recordid, mconfig.getRecordCollection()))
					throw new ResourceNotFoundException("Record not found in Cache.");
				doc = mconfig.getChangeCollection().find(Filters.eq("ediid", recordid)).first() ;
				return (doc != null) ?doc: new Document();
			}
				return commonHelper.mergeDataOnTheFly(recordid, mconfig.getRecordCollection(),mconfig.getChangeCollection());
			} catch (MongoException exp) {
			logger.error("Error while putting updated data in records db" + exp.getMessage());
			throw new CustomizationException("Error updating records (database)" + exp.getMessage());

		}

	}

}
