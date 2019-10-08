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
import java.util.Date;
import java.util.Iterator;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import com.mongodb.Block;
import com.mongodb.MongoException;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Projections;
import com.mongodb.client.model.UpdateOptions;
import com.mongodb.client.model.changestream.ChangeStreamDocument;
import com.mongodb.client.result.DeleteResult;

import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;

/**
 * This class connects to the cache database to get updated record, if the
 * record does not exist in the database, contact Mdserver and getdata.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
@Component
public class DatabaseOperations {
    private static final Logger log = LoggerFactory.getLogger(DatabaseOperations.class);

    @Value("${oar.mdserver:}")
    private String mdserver;

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
		log.error("Input record id is not valid,, check input parameters.");
		throw new IllegalArgumentException("check input parameters.");
	    }
	    long count = mcollection.count(Filters.eq("ediid", recordid));
	    return count != 0;
	} catch (MongoException e) {
	    log.error("Error finding data from MongoDB for requested record id");
	    throw e;
	}
    }

    /**
     * Get data for give recordid
     * 
     * @param recordid
     * @return Document with given id
     * @throws CustomizationException, ResourceNotFoundExceotion
     */
    public Document getData(String recordid, MongoCollection<Document> mcollection)
	    throws ResourceNotFoundException, CustomizationException {
	try {

	    return checkRecordInCache(recordid, mcollection) ? mcollection.find(Filters.eq("ediid", recordid)).first()
		    : getDataFromServer(recordid);
//	    if (checkRecordInCache(recordid, mcollection))
//		return mcollection.find(Filters.eq("ediid", recordid)).first();
//	    else
//		return getDataFromServer(recordid);
	} catch (IllegalArgumentException exp) {
	    log.error("There is an error getting record with given record id. " + exp.getMessage());
	    throw new CustomizationException("There is an error accessing this record." + exp.getMessage());
	} catch (MongoException exp) {
	    log.error("The record requested can not be found." + exp.getMessage());
	    throw new ResourceNotFoundException(
		    "There are errors accessing data and resources requested not found." + exp.getMessage());
	}
    }

    /**
     * 
     * @param recordid
     * @param mcollection
     * @return
     */
    public Document getUpdatedData(String recordid, MongoCollection<Document> mcollection) {
	try {
	    Document changes = new Document();
	    FindIterable<Document> fd = mcollection.find(Filters.eq("ediid", recordid))
		    .projection(Projections.excludeId());
	    Iterator<Document> iterator = fd.iterator();
	    while (iterator.hasNext()) {
		changes = iterator.next();
	    }
	    return changes;
	    // FindIterable<Document> fd = mcollection.find(Filters.eq("ediid",
	    // recordid))
	    // .projection(Projections.include("ediid", "title", "description"));
	    // Iterator<Document> iterator = fd.iterator();
	    // while (iterator.hasNext()) {
	    // Document d = iterator.next();
	    // System.out.println("Document::" + d);
	    // }

	    // // Another tests
	    // mcollection
	    // .watch(Arrays.asList(Aggregates
	    // .match(Filters.in("operationType", Arrays.asList("insert", "update",
	    // "replace", "delete")))))
	    // .fullDocument(FullDocument.UPDATE_LOOKUP).forEach(printBlock);
	} catch (MongoException e) {
	    log.error("Error getting changes from the updated database for given record." + e.getMessage());
	    throw new MongoException("Error Accessing changes from database for the given record." + e.getMessage());
	}
    }

    Block<ChangeStreamDocument<Document>> printBlock = new Block<ChangeStreamDocument<Document>>() {
	@Override
	public void apply(final ChangeStreamDocument<Document> changeStreamDocument) {
	    System.out.println(changeStreamDocument);
	}
    };

    /**
     * This function gets record from mdserver and inserts in the record collection
     * in MongoDB cache database
     * 
     * @param recordid
     * @param mdserver
     * @param mcollection
     * @throws CustomizationException
     * @throws IOException
     */
    public void putDataInCache(String recordid, MongoCollection<Document> mcollection) throws CustomizationException {
	try {
	    Document doc = getDataFromServer(recordid);
	    doc.remove("_id");
	    mcollection.insertOne(doc);
	} catch (MongoException exp) {
	    log.error("Error while putting updated data in cache db" + exp.getMessage());
	    throw new MongoException("Error updating Cache (database)" + exp.getMessage());
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
	    log.error("Error while putting changes in cache db" + ex.getMessage());
	    throw new MongoException("Error while putting changes in cache db." + ex.getMessage());
	}
    }

    /**
     * To update the record in the cached database
     * 
     * @param recordid an ediid of the record
     * @param update   json to update
     * @return Return true if data is updated successfully.
     */
    public boolean updateDataInCache(String recordid, MongoCollection<Document> mcollection, Document update) {
	try {
	    Date now = new Date();
	    update.append("_updateDate", now);

	    if (update.containsKey("_id"))
		update.remove("_id");

	    Document tempUpdateOp = new Document("$set", update);
	    if (tempUpdateOp.containsKey("_id"))
		tempUpdateOp.remove("_id");

	    mcollection.updateOne(Filters.eq("ediid", recordid), tempUpdateOp, new UpdateOptions().upsert(true));

	    return true;
	} catch (MongoException ex) {
	    log.error("Error while update data in cache db" + ex.getMessage());
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
    public boolean deleteRecordInCache(String recordid, MongoCollection<Document> mcollection) {
	try {
	    Document d = mcollection.find(Filters.eq("ediid", recordid)).first();

	    DeleteResult result = mcollection.deleteOne(d);

	    return result.getDeletedCount() == 1 ? true : false;

	} catch (MongoException ex) {
	    log.error("Error deleting data in cache db" + ex.getMessage());
	    throw new MongoException("Error while deleteing data in cache db." + ex.getMessage());
	}

    }

    public Document getDataFromServer(String recordid) throws CustomizationException {
	try {
	    RestTemplate restTemplate = new RestTemplate();
	    return restTemplate.getForObject(mdserver + recordid, Document.class);
	} catch (Exception exp) {
	    log.error("There is an error connecting to backend server to get data" + exp.getMessage());
	    throw new CustomizationException(
		    "There is an error connecting to backend server to get data." + exp.getMessage());
	}
    }

}
