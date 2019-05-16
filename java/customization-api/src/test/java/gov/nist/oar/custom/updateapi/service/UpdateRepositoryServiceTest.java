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

import com.github.fakemongo.junit.FongoRule;
import com.mongodb.AggregationOutput;
import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBObject;
import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.util.FongoJSON;

import gov.nist.oar.custom.updateapi.repositories.UpdateRepository;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.bson.Document;
import org.bson.conversions.Bson;
import org.json.simple.JSONArray;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

/**
 * @author Deoyani Nandrekar-Heinis
 *
 */
//@RunWith(SpringJUnit4ClassRunner.class)

public class UpdateRepositoryServiceTest {
    private Logger logger = LoggerFactory.getLogger(UpdateRepositoryServiceTest.class);

    @Rule
    public FongoRule fongoRule = new FongoRule();
    //DBCollection recordsCollection, changesCollection;

    @Before
    public void initIt() throws Exception {
	

//	recordsCollection = fongoRule.getDB("TestDBtemp").getCollection("recordstest");
//	JSONParser parser = new JSONParser();
//	JSONArray a;
//	File file = new File(this.getClass().getClassLoader().getResource("record.json").getFile());
//	try {
//	    a = (JSONArray) parser.parse(new FileReader(file));
//	    for (Object o : a) {
//		// System.out.println(o.toString());
//		DBObject dbObject = (DBObject) com.mongodb.util.JSON.parse(o.toString());
//		recordsCollection.save(dbObject);
//	    }
//	} catch (IOException | ParseException e) {
//	    // TODO Auto-generated catch block
//	    e.printStackTrace();
//	}
//
//	/// Taxonomy collection;
//	changesCollection = fongoRule.getDB("TestDBtemp").getCollection("changestest");
//	parser = new JSONParser();
//
//	file = new File(this.getClass().getClassLoader().getResource("changes.json").getFile());
//	try {
//	    a = (JSONArray) parser.parse(new FileReader(file));
//	    for (Object o : a) {
//		// System.out.println(o.toString());
//		DBObject dbObject = (DBObject) com.mongodb.util.JSON.parse(o.toString());
//		changesCollection.save(dbObject);
//	    }
//	} catch (IOException | ParseException e) {
//	    // TODO Auto-generated catch block
//	    e.printStackTrace();
//	}
    }

//    // Functions to help test
//    private DBObject dbObject(Bson bson) {
//	if (bson == null) {
//	    return null;
//	}
//
//	// TODO Performance killer
//	return (DBObject) FongoJSON
//		.parse(bson.toBsonDocument(Document.class, MongoClient.getDefaultCodecRegistry()).toString());
//    }
//
    @Test
    public void getData() {

	DataOperations accessData = new DataOperations();
//	accessData.checkRecordInCache("", (MongoCollection<Document>) recordsCollection);

    }
}

/// **
// * This software was developed at the National Institute of Standards and
/// Technology by employees of
// * the Federal Government in the course of their official duties. Pursuant to
/// title 17 Section 105
// * of the United States Code this software is not subject to copyright
/// protection and is in the
// * public domain. This is an experimental system. NIST assumes no
/// responsibility whatsoever for its
// * use by other parties, and makes no guarantees, expressed or implied, about
/// its quality,
// * reliability, or any other characteristic. We would appreciate
/// acknowledgement if the software is
// * used. This software can be redistributed and/or modified freely provided
/// that any derivative
// * works bear some notice that they are derived from it, and any modified
/// versions bear some notice
// * that they have been modified.
// * @author: Deoyani Nandrekar-Heinis
// */
// package gov.nist.oar.rmm.unit.repositories.impl;
//
// import static org.junit.Assert.assertEquals;
//
// import java.io.File;
// import java.io.FileReader;
// import java.io.IOException;
// import java.util.ArrayList;
// import java.util.HashMap;
// import java.util.List;
// import java.util.Map;
//
// import org.bson.Document;
// import org.bson.conversions.Bson;
// import org.json.simple.JSONArray;
// import org.json.simple.parser.JSONParser;
// import org.json.simple.parser.ParseException;
// import org.junit.Before;
// import org.junit.Rule;
// import org.junit.Test;
// import org.junit.runner.RunWith;
// import org.slf4j.Logger;
// import org.slf4j.LoggerFactory;
// import org.springframework.data.domain.Pageable;
// import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
//
// import com.github.fakemongo.junit.FongoRule;
// import com.mongodb.AggregationOutput;
// import com.mongodb.BasicDBObject;
// import com.mongodb.DBCollection;
// import com.mongodb.DBObject;
// import com.mongodb.MongoClient;
// import com.mongodb.util.FongoJSON;
//
// import gov.nist.oar.rmm.unit.repositories.CustomRepositoryTest;
// import gov.nist.oar.rmm.utilities.ProcessRequest;
//
//
// @RunWith(SpringJUnit4ClassRunner.class)
// public class CustomRepositoryImplTest implements CustomRepositoryTest {
//
// private Logger logger =
/// LoggerFactory.getLogger(CustomRepositoryImplTest.class);
// @Rule
// public FongoRule fongoRule = new FongoRule();
// DBCollection recordsCollection, taxonomyCollection;
// @Before
// public void initIt() throws Exception {
//
// recordsCollection =
/// fongoRule.getDB("TestDBtemp").getCollection("recordstest");
// JSONParser parser = new JSONParser();
// JSONArray a;
// File file = new
/// File(this.getClass().getClassLoader().getResource("record.json").getFile());
// try {
// a = (JSONArray) parser.parse(new FileReader(file));
// for (Object o : a)
// {
// //System.out.println(o.toString());
// DBObject dbObject = (DBObject) com.mongodb.util.JSON.parse(o.toString());
// recordsCollection.save(dbObject);
// }
// } catch (IOException | ParseException e) {
// // TODO Auto-generated catch block
// e.printStackTrace();
// }
//
// /// Taxonomy collection;
// taxonomyCollection =
/// fongoRule.getDB("TestDBtemp").getCollection("taxonomytest");
// parser = new JSONParser();
//
// file = new
/// File(this.getClass().getClassLoader().getResource("taxonomy.json").getFile());
// try {
// a = (JSONArray) parser.parse(new FileReader(file));
// for (Object o : a)
// {
// //System.out.println(o.toString());
// DBObject dbObject = (DBObject) com.mongodb.util.JSON.parse(o.toString());
// taxonomyCollection.save(dbObject);
// }
// } catch (IOException | ParseException e) {
// // TODO Auto-generated catch block
// e.printStackTrace();
// }
// }
//
// ////Functions to help test
// private DBObject dbObject(Bson bson) {
// if (bson == null) {
// return null;
// }
//
// // TODO Performance killer
// return (DBObject) FongoJSON.parse(bson.toBsonDocument(Document.class,
/// MongoClient.getDefaultCodecRegistry()).toString());
// }
// @Override
//
// public Document find(Map<String,String> params) {
//
// ProcessRequest request = new ProcessRequest();
// request.parseSearch(params);
//
// //DBObject dQ = (DBObject) request.getFilter();
// long count = 0;
// if(request.getFilter() == null)
// count = recordsCollection.count();
// else{
// Bson b = request.getFilter();
//// DBObject dbobj1 = dbObject(b);
//// DBObject dbobj = new BasicDBObject("$regex","Enterprise");
// count = recordsCollection.count((BasicDBObject)dbObject(b));
// }
//
// logger.info("Count :"+count);
// Document resultDoc = new Document();
// resultDoc.put("ResultCount", count);
// resultDoc.put("PageSize", request.getPageSize());
// //DBObject dbObject = (DBObject) JSON( request.getQueryList());
// List<Bson> dList = request.getQueryList();
// List<BasicDBObject> dobList = new ArrayList<BasicDBObject>();
// int i =0;
// while(dList.size() > i){
// dobList.add( (BasicDBObject)dbObject(dList.get(i)));
// i++;
// }
// AggregationOutput ag = recordsCollection.aggregate(dobList);
// List<DBObject> dlist = new ArrayList<DBObject>();
// for (DBObject dbObject : ag.results()) {
// dlist.add(dbObject);
// }
// resultDoc.put("ResultData",dlist);
// return resultDoc;
// }
//
// @Test
// public void testFindRecords(){
//
// Map<String,String> params = new HashMap<String,String>();
//
// Document r = find(params);
// long resCnt = 134;
// List<DBObject> rdata = (List<DBObject>) r.get("ResultData");
// for (DBObject rd : rdata) {
// System.out.println(rd.get("title"));
// }
// assertEquals(r.get("ResultCount"),resCnt);
// }
//
// @Test
// public void testFindRecordKeyValue(){
// //// Test with parameters
// Map<String,String> params = new HashMap<String,String>();
// params.put("title", "Enterprise Data Inventory");
// Document r1 = find(params);
// List<DBObject> rdata1 = (List<DBObject>) r1.get("ResultData");
// String title = "";
//
// for (DBObject rd : rdata1) {
// title = rd.get("title").toString();
// }
// assertEquals( "Enterprise Data Inventory",title);
//
// }
//
//// @Test
//// public void testFindRecordSearchPhrase(){
//// //// Test with parameters
//// Map<String,String> params = new HashMap<String,String>();
//// params.put("searchphrase", "Enterprise");
//// Document r1 = find(params);
//// List<DBObject> rdata1 = (List<DBObject>) r1.get("ResultData");
//// String title = "";
////
//// for (DBObject rd : rdata1) {
//// title = rd.get("title").toString();
//// }
//// assertEquals( "Enterprise Data Inventory",title);
////
//// }
// @Override
// public List<Document> findtaxonomy(Map<String, String> param) {
// return null;
// }
//
// public List<DBObject> testfindtaxonomy(Map<String, String> param) {
// ProcessRequest request = new ProcessRequest();
//
// List<Document> resultDoc = new ArrayList<Document>();
// //DBObject dQ = (DBObject) request.getFilter();
//
// Bson b = request.parseTaxonomy(param);
// List<DBObject> results =
/// taxonomyCollection.find((BasicDBObject)dbObject(b)).toArray();
//
// return results;
//
// }
//
// @Test
// public void testTaxonomy(){
// Map<String,String> params = new HashMap<String,String>();
// List<DBObject> l = testfindtaxonomy(params);
// assertEquals( 249,l.size());
//
// }
// @Override
// public List<Document> findResourceApis() {
//
// return null;
// }
//
// @Override
// public Document findRecord(String ediid) {
//
// return null;
//
// }
//
// @Override
// public List<Document> findFieldnames() {
//
// return null;
//
// }
//
//
// @Override
// public List<Document> find(Map<String, String> param, Pageable p) {
// return null;
// }
//
// @Override
// public List<Document> findtaxonomy() {
//
// return null;
// }
//
// }
