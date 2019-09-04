package gov.nist.oar.custom.customizationapi.service;
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

import com.mongodb.AggregationOutput;
import com.mongodb.BasicDBObject;
import com.mongodb.DBCollection;
import com.mongodb.DBObject;
import com.mongodb.MongoClient;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;

import gov.nist.oar.custom.customizationapi.config.MongoConfig;
import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;

import static org.junit.Assert.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
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
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.mockito.junit.MockitoJUnitRunner;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * This is a Service test written to check the functions in this class, which are as below:
 * access data from the server or cache
 * update the record with changes in cache
 * submit final changes to publish
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */

@RunWith(MockitoJUnitRunner.Silent.class)
public class UpdateRepositoryServiceTest {
    private Logger logger = LoggerFactory.getLogger(UpdateRepositoryServiceTest.class);

    @InjectMocks
    private UpdateRepositoryService updateService;

    @Mock
    private MongoClient mockClient;
    @Mock
    private MongoCollection<Document> recordCollection;

    @Mock
    private MongoCollection<Document> changesCollection;

    @Mock
    private MongoDatabase mockDB;

    @Mock
    private DataOperations dataOperations;

    @Mock
    private MongoConfig mconfig;

    private String mdserver = "http://testdata.nist.gov/rmm/records/";

    private String changedata;
    private static Document updatedRecord;
    private static String recordid = "FDB5909746815200E043065706813E54137";

    @Before
    public void initMocks() throws IOException, CustomizationException {
	MockitoAnnotations.initMocks(this);
	Mockito.doReturn(recordCollection).when(mconfig).getRecordCollection();
	Mockito.doReturn(changesCollection).when(mconfig).getChangeCollection();
//	ReflectionTestUtils.setField(updateService, "mdserver", "https://testdata.nist.gov/rmm/records/");
	ReflectionTestUtils.setField(dataOperations, "mdserver", "https://testdata.nist.gov/rmm/records/");

    }

    @Test
    public void editTest() throws CustomizationException, IOException {
//	Mockito.doReturn(recordCollection).when(mconfig).getRecordCollection();
//	Mockito.doReturn(changesCollection).when(mconfig).getChangeCollection();
////	ReflectionTestUtils.setField(updateService, "mdserver", "https://testdata.nist.gov/rmm/records/");
//	ReflectionTestUtils.setField(dataOperations, "mdserver", "https://testdata.nist.gov/rmm/records/");

	// when(recordCollection.count()).thenReturn((long) 1);
//	       when(changesCollection.count()).thenReturn((long) 1);
//	when(dataOperations.checkRecordInCache(recordid, recordCollection)).thenReturn(true);

//	
	File file = new File(this.getClass().getClassLoader().getResource("record.json").getFile());
	String recorddata = new String(
		Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("record.json").getFile())));
	Document recordDoc = Document.parse(recorddata);

//	       when(dataOperations.getData(recordid, recordCollection, mdserver)).thenReturn(recordDoc);
	when(dataOperations.getData(recordid, recordCollection)).thenReturn(recordDoc);

//	       FindIterable iterable = mock(FindIterable.class);
//	       MongoCursor cursor = mock(MongoCursor.class);
//	       Document bob = new Document("_id",new ObjectId("579397d20c2dd41b9a8a09eb"))
//	          .append("firstName", "Bob")
//	          .append("lastName", "Bobberson");

//	       when(recordCollection.find(Filters.eq("ediid", recordid)))
//	          .thenReturn(iterable);
//	       when(iterable.iterator()).thenReturn(cursor);
//	       when(cursor.hasNext()).thenReturn(true).thenReturn(false);
//	       when(cursor.next()).thenReturn(recordDoc);

//	       when(dataOperations.getData(recordid, changesCollection, mdserver)).thenReturn(updatedRecord);

	Document doc = updateService.edit(recordid);
	assertNotNull(doc);
	assertEquals("New Title Update Test May 7", doc.get("title"));
	assertNotEquals("New Title Update Test May 14", doc.get("title"));
    }

    @Test
    public void updateRecordTest() throws CustomizationException, IOException {

	changedata = new String(
		Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("changes.json").getFile())));
	Document change = Document.parse(changedata);

	String updateddata = new String(Files
		.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("updatedRecord.json").getFile())));
	updatedRecord = Document.parse(updateddata);
	// when(dataOperations.getUpdatedData(updateddata,
	// recordCollection)).thenReturn(updatedRecord);
	when(dataOperations.updateDataInCache(recordid, recordCollection, change)).thenReturn(true);
	when(dataOperations.updateDataInCache(recordid, changesCollection, change)).thenReturn(true);
	when(dataOperations.getData(recordid, recordCollection)).thenReturn(updatedRecord);

	Document doc = updateService.update(changedata, recordid);
	assertNotNull(doc);
	assertEquals("New Title Update Test May 14", doc.get("title"));
    }

    @Test
    public void saveRecordTest() throws IOException {
	changedata = new String(
		Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("changes.json").getFile())));
	Document change = Document.parse(changedata);

	String updateddata = new String(Files
		.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("updatedRecord.json").getFile())));
	updatedRecord = Document.parse(updateddata);
	// when(dataOperations.getUpdatedData(updateddata,
	// recordCollection)).thenReturn(updatedRecord);
	when(dataOperations.updateDataInCache(recordid, recordCollection, change)).thenReturn(true);
	when(dataOperations.updateDataInCache(recordid, changesCollection, change)).thenReturn(true);
	when(dataOperations.getUpdatedData(recordid, changesCollection)).thenReturn(updatedRecord);
	Document doc = updateService.save(recordid, changedata);
	assertNotNull(doc);
	assertEquals("New Title Update Test May 14", doc.get("title"));
    }

}
