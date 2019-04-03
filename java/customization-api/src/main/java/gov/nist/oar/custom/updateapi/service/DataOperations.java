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
package gov.nist.oar.custom.updateapi.service;

import java.util.Iterator;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestTemplate;

import com.mongodb.Block;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Projections;
import com.mongodb.client.model.changestream.ChangeStreamDocument;
import com.mongodb.client.result.UpdateResult;

/**
 * This class connects to the cache database to get updated record, if the
 * record does not exist in the database, contact Mdserver and getdata.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class DataOperations {
    private static final Logger log = LoggerFactory.getLogger(DataOperations.class);

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

	@SuppressWarnings("deprecation")
	long count = mcollection.count(Filters.eq("ediid", recordid));
	return count != 0;

    }

    /**
     * Get data for give recordid
     * 
     * @param recordid
     * @return
     */
    public Document getData(String recordid, MongoCollection<Document> mcollection, String mdserver) {
	if (checkRecordInCache(recordid, mcollection))
	    return mcollection.find(Filters.eq("ediid", recordid)).first();
	else
	    return this.getDataFromServer(recordid, mdserver);
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
     * 
     * @param recordid
     * @return
     */
    public Document getDataFromServer(String recordid, String mdserver) {
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
    public void putDataInCache(String recordid, String mdserver, MongoCollection<Document> mcollection) {
	Document doc = getDataFromServer(recordid, mdserver);
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
     * 
     * @param recordid
     * @param update
     * @return
     */
    public boolean updateDataInCache(String recordid, MongoCollection<Document> mcollection, Document update) {

	Document tempUpdateOp = new Document("$set", update);
	UpdateResult updates = mcollection.updateOne(Filters.eq("ediid", recordid), tempUpdateOp);
	return updates != null;
    }
}
