package gov.nist.oar.custom.customizationapi.service;

import java.io.IOException;

import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPatch;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.bson.Document;
import org.bson.json.JsonMode;
import org.bson.json.JsonWriterSettings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.web.client.RestTemplate;

import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;

/**
 * This class connected to backend metadata server to get data or send the
 * updated data.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class BackendServerOperations {

    private static final Logger log = LoggerFactory.getLogger(BackendServerOperations.class);

    String mdserver;
    String mdsecret;

    public BackendServerOperations() {
    }

    public BackendServerOperations(String mdserver, String mdsecret) {

	this.mdserver = mdserver;
	this.mdsecret = mdsecret;
    }

    /**
     * Connects to backed metadata server to get the data
     * 
     * @param recordid
     * @return
     * 
     */
    public Document getDataFromServer(String mdserver, String recordid) throws IOException {
	log.info("Call backend metadata server.");

	RestTemplate restTemplate = new RestTemplate();
	return restTemplate.getForObject(mdserver + recordid, Document.class);
    }

    /***
     * Send changes made in cached record to the back end metadata server
     * 
     * @param recordid string ediid/unique record id
     * @param doc      changes to be sent
     * @return Updated record
     * @throws CustomizationException
     *
     */
    public Document sendChangesToServer(String recordid, Document doc) throws CustomizationException {
	log.info("Send changes to backend metadataserver");
	Document updatedDoc = null;
	CloseableHttpResponse response = null;
	try {

	    HttpClient httpClient = HttpClients.createDefault();
	    HttpPatch httppatch = new HttpPatch(mdserver + recordid);
	    httppatch.addHeader("Authorization", "Bearer " + this.mdsecret);
	    httppatch.addHeader("Content-Type", "application/json");
	   
	    JsonWriterSettings writerSettings = new JsonWriterSettings(JsonMode.SHELL, true);
//	    System.out.println(doc.toJson(writerSettings)+ "\n"+doc.toJson()+"\n"+doc.toString());
	    StringEntity jsonEntity = new StringEntity(doc.toJson(writerSettings));
	    httppatch.setEntity(jsonEntity);
	    response = (CloseableHttpResponse) httpClient.execute(httppatch);
	    String responseBody = EntityUtils.toString(response.getEntity());
	    updatedDoc = Document.parse(responseBody);
	    return updatedDoc;

	} catch (Exception exp) {
	    log.error("There is an error getting response from the server." + exp.getMessage());
	    throw new CustomizationException("Error getting response from server." + exp.getMessage());

	} finally {
	    try {
		if (response != null)
		    response.close();
	    } catch (IOException e) {
		log.error(" Error closing the response in send data to server.");
		// e.printStackTrace();
	    }
	}
    }

    /***
     * Check if service is authorized to make changes in backend metadata server
     * 
     * @param recordid String ediid/unique record id
     * @return Information about authorized user
     */
    public Document getAuthorization(String recordid) {
	log.info("Check if it is authorized to change data");
	RestTemplate restTemplate = new RestTemplate();
	HttpHeaders headers = new HttpHeaders();
	headers.add("Authorization", "Bearer " + this.mdsecret);
	return restTemplate.getForObject(mdserver + recordid, Document.class);
    }
}
