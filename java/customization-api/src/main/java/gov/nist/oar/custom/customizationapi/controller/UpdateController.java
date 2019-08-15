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
package gov.nist.oar.custom.customizationapi.controller;

import java.io.IOException;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;

//import org.apache.http.HttpEntity;
//import org.apache.http.HttpResponse;
//import org.apache.http.NameValuePair;
//import org.apache.http.client.ClientProtocolException;
//import org.apache.http.client.HttpClient;
//import org.apache.http.client.entity.UrlEncodedFormEntity;
//import org.apache.http.client.methods.HttpPost;
//import org.apache.http.impl.client.HttpClients;
//import org.apache.http.message.BasicNameValuePair;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.exceptions.ErrorInfo;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * Controller to update 
 * @author  Deoyani Nandrekar-Heinis
 *
 */
@RestController
@Api(value = "Api endpoints to access editable data, update changes to data, save in the backend", tags = "Customization API")
@Validated
@RequestMapping("/")
public class UpdateController {
    private Logger logger = LoggerFactory.getLogger(UpdateController.class);

    @Autowired
    private HttpServletRequest request;

    @Autowired
    private UpdateRepository uRepo;
    
 
    @RequestMapping(value = {
	    "update/{ediid}" }, method = RequestMethod.POST)
    @ApiOperation(value = ".", nickname = "Cache Record Changes", notes = "Resource returns a record if it is editable and user is authenticated.")
    public Document updateRecord(@PathVariable @Valid String ediid,
	    @Valid @RequestBody String params)  throws CustomizationException {

	logger.info("Update the given record: "+ ediid);
	return uRepo.update(params, ediid);
	
    }

    @RequestMapping(value = {
	    "save/{ediid}" }, method = RequestMethod.POST)
    @ApiOperation(value = ".", nickname = "Save changes to server", notes = "Resource returns a boolean based on success or failure of the request.")
    public Document saveRecord(@PathVariable @Valid String ediid,  @Valid @RequestBody String params) throws CustomizationException {
	logger.info("Send updated record to mdserver:"+ediid);
	return uRepo.save(ediid, params);
//	RestTemplate restTemplate = new RestTemplate();
//	HttpHeaders headers = new HttpHeaders();
//	headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
//
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

    @RequestMapping(value = {
	    "edit/{ediid}" }, method = RequestMethod.GET)
    @ApiOperation(value = ".", nickname = "Access editable Record", notes = "Resource returns a record if it is editable and user is authenticated.")
    public Document editRecord(@PathVariable @Valid String ediid) {
	logger.info("Access the record to be edited by ediid "+ediid);
	return uRepo.edit(ediid);
    }
    
    @ExceptionHandler(IOException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorInfo handleStreamingError(CustomizationException ex, HttpServletRequest req) {
	logger.info("There is an error accessing data: " + req.getRequestURI() + "\n  " + ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 500, "Internal Server Error", "POST");
    }

    @ExceptionHandler(RuntimeException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)

    public ErrorInfo handleStreamingError(RuntimeException ex, HttpServletRequest req) {
	logger.error("Unexpected failure during request: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
	return new ErrorInfo(req.getRequestURI(), 500, "Unexpected Server Error");
    }
}
