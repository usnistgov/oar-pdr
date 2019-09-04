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

import java.util.Date;
import java.util.Iterator;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import com.mongodb.Block;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Projections;
import com.mongodb.client.model.changestream.ChangeStreamDocument;
import com.mongodb.client.result.DeleteResult;
import com.mongodb.client.result.UpdateResult;

/**
 * This class connects to the cache database to get updated record, if the
 * record does not exist in the database, contact Mdserver and getdata.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
@Component
public class DataOperations {
    private static final Logger log = LoggerFactory.getLogger(DataOperations.class);
    
 
    @Value("${oar.mdserver:}")
    private String mdserver;

    

    /**
     * Check whether record exists in updated database
     * 
     * @param recordid
     * @return
     */
    public boolean checkRecordInCache(String recordid, MongoCollection<Document> mcollection) {
	Pattern p = Pattern.compile("[^a-z0-9]", Pattern.CASE_INSENSITIVE);
	Matcher m = p.matcher(recordid);
	if (m.find()) {
	    log.error("Input record id is not valid,, check input parameters.");
	    throw new IllegalArgumentException("check input parameters.");
	}
	long count = mcollection.count(Filters.eq("ediid", recordid));
	return count != 0;
    }
    
//    public Document getData(String recordid, MongoCollection<Document> mcollection) {
//	
//	try {
//	if (checkRecordInCache(recordid, mcollection))
//	    return mcollection.find(Filters.eq("ediid", recordid)).first();
//	else
//	    return this.getDataFromServer(recordid);
//	}catch(Exception exp) {
//	    throw new ResourceNotFoundException("There are errors accessing data and resources requested not found."+exp.getMessage());
//	}
////	return new Document();
//    }

    /**
//     * Get data for give recordid
//     * 
//     * @param recordid
//     * @return
//     */
    public Document getData(String recordid, MongoCollection<Document> mcollection) throws ResourceNotFoundException {
	try {
	if (checkRecordInCache(recordid, mcollection))
	    return mcollection.find(Filters.eq("ediid", recordid)).first();
	else
	    return this.getDataFromServer(recordid);
	}catch(Exception exp) {
	    throw new ResourceNotFoundException("There are errors accessing data and resources requested not found."+exp.getMessage());
	}	
    }

    public Document getUpdatedData(String recordid, MongoCollection<Document> mcollection) {

	Document changes = new Document();
	FindIterable<Document> fd = mcollection.find(Filters.eq("ediid", recordid)).projection(Projections.excludeId());
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
    }

    Block<ChangeStreamDocument<Document>> printBlock = new Block<ChangeStreamDocument<Document>>() {
	@Override
	public void apply(final ChangeStreamDocument<Document> changeStreamDocument) {
	    System.out.println(changeStreamDocument);
	}
    };

    /**
     * Connects to backed metadata server to get the data
     * @param recordid
     * @return
     */
    public Document getDataFromServer(String recordid) {
	
	RestTemplate restTemplate = new RestTemplate();
	return restTemplate.getForObject(mdserver + recordid, Document.class);
    }

    /**
     * This function gets record from mdserver and inserts in the record
     * collection in MongoDB cache database
     * 
     * @param recordid
     * @param mdserver
     * @param mcollection
     */
    public void putDataInCache(String recordid, MongoCollection<Document> mcollection) {
	Document doc = getDataFromServer(recordid);
	doc.remove("_id");
	mcollection.insertOne(doc);
    }

    /**
     * This function inserts updated record changes in the Mongodb changes
     * collection.
     * 
     * @param update
     * @param mcollection
     */
    public void putDataInCacheOnlyChanges(Document update, MongoCollection<Document> mcollection) {
	mcollection.insertOne(update);
    }

    /**
     * To update the record in the cached database
     * @param recordid an ediid of the record
     * @param update json to update
     * @return Return true if data is updated successfully.
     */
    public boolean updateDataInCache(String recordid, MongoCollection<Document> mcollection, Document update) {
	Date now = new Date();
	update.append("_updateDate", now);
	Document tempUpdateOp = new Document("$set", update);
	tempUpdateOp.remove("_id");
	//BasicDBObject timeNow = new BasicDBObject("date", now);
	UpdateResult updates = mcollection.updateOne(Filters.eq("ediid", recordid), tempUpdateOp);
	//return updates != null;
	return true;
    }
    
    /**
     * Find the record of given id in the collection and remove.
     * @param recordid Unique record identifier
     * @param mcollection MongoDB Collection
     * @return true if the record is deleted successfully.
     */
    public boolean deleteRecordInCache(String recordid, MongoCollection<Document> mcollection) {
	Document d = mcollection.find(Filters.eq("ediid", recordid)).first();
	
	DeleteResult result = mcollection.deleteOne(d);
	if (result.getDeletedCount() == 1) {
		return true;
	} else {
		return false;
	}

    }
}
