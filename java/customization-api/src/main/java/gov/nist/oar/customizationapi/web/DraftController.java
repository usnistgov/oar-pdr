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
package gov.nist.oar.customizationapi.web;

import java.io.IOException;
//import java.util.Optional;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.InternalAuthenticationServiceException;
//import org.springframework.security.authentication.InternalAuthenticationServiceException;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;

import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.ErrorInfo;
import gov.nist.oar.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.customizationapi.repositories.DraftService;
//import gov.nist.oar.customizationapi.repositories.UpdateRepository;
import gov.nist.oar.customizationapi.service.ResourceNotFoundException;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * This is a webservice/restapi controller which gives access to customization cache database.
 * On behalf of MIDAS the metadata server can put data or record, delete or access it whenever needed.
 * There are three end points provided in this, each
 * dealing with specific tasks. In OAR project internal landing page for the edi
 * record is accessed using backed metadata. This metadata is a advanced POD
 * record called NERDm.  This webservice connects to backend MongoDB which holds the
 * record being edited. The service needs an authorized token to access these endpoints.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
@RestController
@Api(value = "Api endpoints to access editable data, update changes to data, save in the backend", tags = "Customization API")
//@Validated
@RequestMapping("/pdr/lp/draft/")
public class DraftController {
	private Logger logger = LoggerFactory.getLogger(DraftController.class);

	@Autowired
	private DraftService draftRepo;

	@Value("${custom.service.secret:testtoken}")
	String authorization;

	/***
	 * Get complete record or only the changes made to the record by providing
	 * 'view=updates' option.
	 * 
	 * @param ediid Unique record identifier
	 * @return Document
	 * @throws CustomizationException
	 */
	@RequestMapping(value = { "{ediid}" }, method = RequestMethod.GET, produces = "application/json")
	@ApiOperation(value = ".", nickname = "Access editable Record", notes = "Resource returns a record if it is editable and user is authenticated.")
	public Document getData(@PathVariable @Valid String ediid, @RequestParam(required = false) String view,
			@RequestHeader("Authorization") String serviceAuth) throws CustomizationException {
		logger.info("Access the record to be edited by ediid " + ediid);
		if (!serviceAuth.equals(authorization))
			throw new InternalAuthenticationServiceException("Service is not authorized to access this record.");
		String viewoption = "";
		if (view != null && !view.equals(""))
			viewoption = view;
		return draftRepo.getDraft(ediid, viewoption);
	}

	/**
	 * Delete the resource from staging area/cache
	 * 
	 * @param ediid Unique record identifier
	 * @return JSON document original format
	 * @throws CustomizationException
	 */
	@RequestMapping(value = { "{ediid}" }, method = RequestMethod.DELETE, produces = "application/json")
	@ApiOperation(value = ".", nickname = "Delete the Record from drafts", notes = "This will allow user to delete all the changes made in the record in draft mode, original published record will remain as it is.")
	public boolean deleteRecord(@PathVariable @Valid String ediid, @RequestHeader("Authorization") String serviceAuth)
			throws CustomizationException {
		logger.info("Delete the record from stagging given by ediid " + ediid);
		if (!serviceAuth.equals(authorization))
			throw new InternalAuthenticationServiceException("Service is not authorized to access this record.");

		return draftRepo.deleteDraft(ediid);
	}

	/**
	 * Metadata server send data over to store in the cache/staging area until editing is done and finalized by 
	 * client application.
	 * 
	 * @param ediid  Unique record id
	 * @param params Modified fields in JSON
	 * @return Updated JSON record
	 * @throws CustomizationException
	 * @throws InvalidInputException
	 */
	@RequestMapping(value = {
			"{ediid}" }, method = RequestMethod.PUT, headers = "accept=application/json", produces = "application/json")
	@ApiOperation(value = ".", nickname = "Save changes to server", notes = "Resource returns a boolean based on success or failure of the request.")
	@ResponseStatus(HttpStatus.CREATED)
	public void createRecord(@PathVariable @Valid String ediid, @Valid @RequestBody Document params,
			@RequestHeader("Authorization") String serviceAuth)
			throws CustomizationException, InvalidInputException, ResourceNotFoundException {
		logger.info("Send updated record to backend metadata server:" + ediid);
		if (!serviceAuth.equals(authorization))
			throw new InternalAuthenticationServiceException("Service is not authorized to access this record.");
		draftRepo.putDraft(ediid, params);

	}

	/**
	 * If there is an internal error due to certain functions failue this is called.
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(CustomizationException.class)
	@ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
	public ErrorInfo handleCustomization(CustomizationException ex, HttpServletRequest req) {
		logger.error("There is an error in the service: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
		return new ErrorInfo(req.getRequestURI(), 500, "Internal Server Error");
	}

	/**
	 * If record is not available in the database
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(ResourceNotFoundException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	public ErrorInfo handleStreamingError(ResourceNotFoundException ex, HttpServletRequest req) {
		logger.info("There is an error accessing requested record : " + req.getRequestURI() + "\n  " + ex.getMessage());
		return new ErrorInfo(req.getRequestURI(), 404, "Resource Not Found", req.getMethod());
	}

	/**
	 * If input is not of allowed format
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(InvalidInputException.class)
	@ResponseStatus(HttpStatus.BAD_REQUEST)
	public ErrorInfo handleStreamingError(InvalidInputException ex, HttpServletRequest req) {
		logger.info("There is an error processing input data: " + req.getRequestURI() + "\n  " + ex.getMessage());
		return new ErrorInfo(req.getRequestURI(), 400, "Invalid input error", "PATCH");
	}

	/**
	 * Some generic exception thrown by service
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(IOException.class)
	@ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
	public ErrorInfo handleStreamingError(CustomizationException ex, HttpServletRequest req) {
		logger.info("There is an error accessing data: " + req.getRequestURI() + "\n  " + ex.getMessage());
		return new ErrorInfo(req.getRequestURI(), 500, "Internal Server Error", "POST");
	}

	/**
	 * If there is any runtime error
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(RuntimeException.class)
	@ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)

	public ErrorInfo handleStreamingError(RuntimeException ex, HttpServletRequest req) {
		logger.error("Unexpected failure during request: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
		return new ErrorInfo(req.getRequestURI(), 500, "Unexpected Server Error");
	}

	/**
	 * If backend server , IDP or metadata server is not working it wont authorized
	 * the user but it will throw an exception.
	 * 
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(RestClientException.class)
	@ResponseStatus(HttpStatus.BAD_GATEWAY)
	public ErrorInfo handleRestClientError(RuntimeException ex, HttpServletRequest req) {
		logger.error("Unexpected failure during request: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
		return new ErrorInfo(req.getRequestURI(), 502, "Can not connect to backend server");
	}

	/**
	 * Handles internal authentication service exception if user is not authorized
	 * or token is expired
	 * 
	 * @param ex
	 * @param req
	 * @return
	 */
	@ExceptionHandler(InternalAuthenticationServiceException.class)
	@ResponseStatus(HttpStatus.UNAUTHORIZED)
	public ErrorInfo handleRestClientError(InternalAuthenticationServiceException ex, HttpServletRequest req) {
		logger.error("Unauthorized user or token : " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
		return new ErrorInfo(req.getRequestURI(), 401, "Untauthorized token used to acces the service.");
	}
}
