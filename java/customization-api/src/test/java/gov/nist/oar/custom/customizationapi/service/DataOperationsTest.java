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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.bson.Document;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.mockito.junit.MockitoJUnitRunner;
import org.springframework.test.util.ReflectionTestUtils;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;

import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;

/**
 * This class contains unit tests for different methods/functions available in DataOperations class
 * This class deals with checking and updating records in the cache and send final updates to backend server
 * @author Deoyani Nandrekar-Heinis
 *
 */
@RunWith(MockitoJUnitRunner.Silent.class)
public class DataOperationsTest {

    @Mock
    private MongoClient mockClient;
    @Mock
    private MongoCollection<Document> mockCollection;
    
    @Mock
    private MongoCollection<Document> mockChangeCollection;
    
    @Mock
    private MongoDatabase mockDB;
    
//    private String mdserver = "http://testdata.nist.gov/rmm/records/";
    private static DatabaseOperations mockDataOperations;
    private static Document change;
    private static Document updatedRecord;
    private static String recordid ="FDB5909746815200E043065706813E54137";


    @Before
    public void initMocks() throws IOException, ResourceNotFoundException, CustomizationException {
	mockDataOperations = mock(DatabaseOperations.class);
       when(mockClient.getDatabase("UpdateDB")).thenReturn(mockDB);
       when(mockDB.getCollection("record")).thenReturn(mockCollection);
       when(mockDB.getCollection("change")).thenReturn(mockChangeCollection);
       ReflectionTestUtils.setField(mockDataOperations, "mdserver", "https://testdata.nist.gov/rmm/records/");

       String recorddata = new String ( Files.readAllBytes( 
	       Paths.get(
		       this.getClass().getClassLoader().getResource("record.json").getFile())));
       Document recordDoc = Document.parse(recorddata);
       
       String changedata = new String ( Files.readAllBytes( 
	       Paths.get(
		       this.getClass().getClassLoader().getResource("changes.json").getFile())));
       change = Document.parse(changedata);
       
       String updateddata = new String ( Files.readAllBytes( 
	       Paths.get(
		       this.getClass().getClassLoader().getResource("updatedRecord.json").getFile())));
       updatedRecord = Document.parse(updateddata);
        
      MockitoAnnotations.initMocks(this);
      when(mockDataOperations.getData(recordid, mockCollection)).thenReturn(recordDoc);
      when(mockDataOperations.getUpdatedData(recordid, mockCollection)).thenReturn(updatedRecord); 
      when(mockDataOperations.getUpdatedData(recordid, mockChangeCollection)).thenReturn(change); 
      when(mockDataOperations.checkRecordInCache(recordid, mockCollection)).thenReturn(true);
//      when(mockDataOperations.putDataInCacheOnlyChanges(change, mockChangeCollection)).thenReturn(recordDoc);

    }
    
    @Test
    public void testGetData() throws ResourceNotFoundException, CustomizationException{
	Document d = mockDataOperations.getData(recordid, mockCollection);
	assertNotNull(d);
        assertEquals("New Title Update Test May 7", d.get("title"));
    }
    
    @Test
    public void testPutDataInCacheOnlyChanges(){
	mockDataOperations.putDataInCacheOnlyChanges(change, mockChangeCollection);
	Document updatedRecord = mockDataOperations.getUpdatedData(recordid, mockChangeCollection);
	assertNotNull(updatedRecord);
	assertNotEquals("New Title Update Test May 7", updatedRecord.get("title"));
	assertEquals("New Title Update Test May 14", updatedRecord.get("title"));	
    }
   
    @Test
    public void testCheckRecordInCache(){
	boolean isPresent = mockDataOperations.checkRecordInCache(recordid, mockCollection);
	assertEquals(isPresent, true);
    }
    
    @Test
    public void testUpdatedDataInCache() throws CustomizationException{
	mockDataOperations.putDataInCache(recordid, mockCollection);
	Document updatedRecord = mockDataOperations.getUpdatedData(recordid, mockCollection);
	assertNotNull(updatedRecord);
	assertEquals("New Title Update Test May 14", updatedRecord.get("title"));
    }
}
