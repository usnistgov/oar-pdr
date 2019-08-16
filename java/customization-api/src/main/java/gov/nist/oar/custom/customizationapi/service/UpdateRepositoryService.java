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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.mongodb.client.MongoCollection;

import gov.nist.oar.custom.customizationapi.config.MongoConfig;
import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;

/**
 * UpdateRepository is the service class which takes input from client to edit
 * or update records in cache database. The funtions are written to process 
 * @author Deoyani Nandrekar-Heinis
 */
@Service
public class UpdateRepositoryService implements UpdateRepository {

    private Logger logger = LoggerFactory.getLogger(UpdateRepositoryService.class);
    @Autowired
    MongoConfig mconfig;
   
    @Value("${oar.mdserver:}")
    private String mdserver;

    MongoCollection<Document> recordCollection;
    MongoCollection<Document> changesCollection;
    DataOperations accessData = new DataOperations();


    /**
     * Update the input json changes by client in the cache mongo database.
     * 
     * @throws CustomizationException
     */
    @Override
    public Document update(String params, String recordid) throws CustomizationException {
	if (processInputHelper(params, recordid))
	    return accessData.getData(recordid, recordCollection, mdserver);
	else
	    throw new CustomizationException("Input Request could not processed successfully.");
    }

    /**
     * Process input json, check against the json schema defined for the
     * specific fields.
     * 
     * @param params
     * @param recordid
     * @return
     */
    private boolean processInputHelper(String params, String recordid) {
	ProcessInputRequest req = new ProcessInputRequest();
	if (req.validateInputParams(params)) {

	    // this.accessData.checkRecordInCache(recordid, recordCollection);
	    Document update = Document.parse(params);
	    update.remove("_id");
	    update.append("ediid", recordid);
	    return this.updateHelper(recordid, update);
	    // return accessData.updateDataInCache(recordid, recordCollection,
	    // update);
	} else
	    return false;
    }

    /**
     * UpdateHelper takes input recordid and json input, this function checks if
     * the record is there in cache If not it pulls record and puts in cache and
     * then update the changes.
     * 
     * @param recordid
     * @param update
     * @return
     */
    private boolean updateHelper(String recordid, Document update) {

	recordCollection = mconfig.getRecordCollection();
	changesCollection = mconfig.getChangeCollection();

	if (!this.accessData.checkRecordInCache(recordid, recordCollection))
	    this.accessData.putDataInCache(recordid, mdserver, recordCollection);

	if (!this.accessData.checkRecordInCache(recordid, changesCollection))
	    this.accessData.putDataInCacheOnlyChanges(update, changesCollection);

	return accessData.updateDataInCache(recordid, recordCollection, update)
		&& accessData.updateDataInCache(recordid, changesCollection, update);

    }

    /**
     * accessing records to edit in the front end.
     */
    @Override
    public Document edit(String recordid) {
	recordCollection = mconfig.getRecordCollection();
	changesCollection = mconfig.getChangeCollection();
	return accessData.getData(recordid, recordCollection, mdserver);
    }

    /**
     * Save action can accept changes and save them or just return the updated
     * data from cache.
     */
    @Override
    public Document save(String recordid, String params) {
	recordCollection = mconfig.getRecordCollection();
	changesCollection = mconfig.getChangeCollection();
	if (!(params.isEmpty() || params == null) && !processInputHelper(params, recordid))
	    return null;
	return accessData.getUpdatedData(recordid, changesCollection);

    }

}
