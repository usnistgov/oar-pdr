package gov.nist.oar.custom.customizationapi.service;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.client.RestTemplate;
//import org.apache.http.HttpEntity;
//import org.apache.http.HttpResponse;
//import org.apache.http.NameValuePair;
//import org.apache.http.client.ClientProtocolException;
//import org.apache.http.client.HttpClient;
//import org.apache.http.client.entity.UrlEncodedFormEntity;
//import org.apache.http.client.methods.HttpPost;
//import org.apache.http.impl.client.HttpClients;
//import org.apache.http.message.BasicNameValuePair;

/**
 * This class connected to backend metadata server to get data or send the updated data.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class BackendServerOperations {
    
    private static final Logger log = LoggerFactory.getLogger(BackendServerOperations.class);
  
  
    String mdserver;
    String mdsecret;
    
    public BackendServerOperations() {}
    
    public BackendServerOperations(String mdserver, String mdsecret ) {
	
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
    public Document getDataFromServer(String mdserver, String recordid) {
	log.info("Call backend metadata server.");

	RestTemplate restTemplate = new RestTemplate();
	return restTemplate.getForObject(mdserver + recordid, Document.class);
    }
    
    /***
     * Send changes made in cached record to the backend metadata server
     * 
     * @param recordid string ediid/unique record id
     * @param doc changes to be sent
     * @return Updated record 
     */
    public Document sendChangesToServer(String recordid, Document doc){
	log.info("Send changes to backend metadataserver");
	RestTemplate restTemplate = new RestTemplate();	
	HttpHeaders headers = new HttpHeaders();
	headers.add("Authorization", "Bearer "+this.mdsecret);
	HttpEntity<Document> requestUpdate = new HttpEntity<>(doc, headers);
	Document updatedDoc = (Document) restTemplate.patchForObject(mdserver+recordid, requestUpdate,
		Document.class);
	
	return updatedDoc;
	
//	HttpHeaders headers = new HttpHeaders();
//	headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

//	MultiValueMap<String, String> map= new LinkedMultiValueMap<String, String>();
//	map.add("email", "first.last@example.com");
//
//	HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<MultiValueMap<String, String>>(map, headers);
//
//	ResponseEntity<String> response = restTemplate.postForEntity( "", request , String.class );

//	HttpClient httpclient = HttpClients.createDefault();
//	HttpPost httppost = new HttpPost("server");
//
//	// Request parameters and other properties.
//	List<NameValuePair> params = new ArrayList<NameValuePair>(2);
//	params.add(new BasicNameValuePair("Authorization", "12345"));
//	params.add(new BasicNameValuePair("Content-type", "application/json"));
//	httppost.setEntity(new UrlEncodedFormEntity(params, "UTF-8"));
//
//	//Execute and get the response.
//	HttpResponse response = httpclient.execute(httppost);
//	HttpEntity entity = response.getEntity();
//
//	if (entity != null) {
//	    try (InputStream instream = entity.getContent()) {
//	        // do something useful
//	    }
//	}

	
    }
    /***
     * Check if service is authorized to make changes in backend metadata server
     * @param recordid String ediid/unique record id
     * @return Information about authorized user
     */
    public Document getAuthorization(String recordid) {
	log.info("Check if it is authorized to change data");
	RestTemplate restTemplate = new RestTemplate();
	HttpHeaders headers = new HttpHeaders();
	headers.add("Authorization", "Bearer "+this.mdsecret);
	return restTemplate.getForObject(mdserver + recordid, Document.class);
    }
}
