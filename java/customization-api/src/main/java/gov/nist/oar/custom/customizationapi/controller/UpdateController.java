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

import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;

import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.exceptions.ErrorInfo;
import gov.nist.oar.custom.customizationapi.exceptions.InvalidInputException;
import gov.nist.oar.custom.customizationapi.repositories.UpdateRepository;
import gov.nist.oar.custom.customizationapi.service.ResourceNotFoundException;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;

/**
 * This is a webservice/restapi controller which gives options to access, update
 * and delete the record. There are four end points provided in this, each
 * dealing with specific tasks. In OAR project internal landing page for the edi
 * record is accessed using backed metadata. This metadata is a advanced POD
 * record called NERDm. In this api we are allowing the record to be modified by
 * authorized user. This webservice connects to backend MongoDB which holds the
 * record being edited. When the record is accessed for the first time, it is
 * fetched from backend metadata service. If it gets modified the updated record
 * is saved in this stagging database until finalzed Once it is finalized it is
 * pushed back to backend service to merge and send to review.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
@RestController
@Api(value = "Api endpoints to access editable data, update changes to data, save in the backend", tags = "Customization API")
@Validated
@RequestMapping("/api")
public class UpdateController {
    private Logger logger = LoggerFactory.getLogger(UpdateController.class);


    @Autowired
    private UpdateRepository uRepo;

    /**
     * Update the fields of record metadata.
     * 
     * @param ediid  unique record id
     * @param params subset of metadata modified in JSON format
     * @return Updated record in JSON format
     * @throws CustomizationException
     * @throws InvalidInputException
     */
    @RequestMapping(value = {
	    "draft/{ediid}" }, method = RequestMethod.PATCH, headers = "accept=application/json", produces = "application/json")
    @ApiOperation(value = ".", nickname = "Cache Record Changes", notes = "Resource returns a record if it is editable and user is authenticated.")
    public Document updateRecord(@PathVariable @Valid String ediid, @Valid @RequestBody String params)
	    throws CustomizationException, InvalidInputException {

	logger.info("Update the given record: " + ediid);
	return uRepo.update(params, ediid);

    }

    /***
     * Access the record from service
     * 
     * @param ediid Unique record identifier
     * @return
     * @throws CustomizationException
     */
    @RequestMapping(value = { "draft/{ediid}" }, method = RequestMethod.GET, produces = "application/json")
    @ApiOperation(value = ".", nickname = "Access editable Record", notes = "Resource returns a record if it is editable and user is authenticated.")
    public Document editRecord(@PathVariable @Valid String ediid) throws CustomizationException {
	logger.info("Access the record to be edited by ediid " + ediid);
	return uRepo.edit(ediid);
    }

    /**
     * Delete the resource from staging area
     * 
     * @param ediid Unique record identifier
     * @return JSON document original format
     * @throws CustomizationException
     */
    @RequestMapping(value = { "draft/{ediid}" }, method = RequestMethod.DELETE, produces = "application/json")
    @ApiOperation(value = ".", nickname = "Delete the Record from drafts", notes = "This will allow user to delete all the changes made in the record in draft mode, original published record will remain as it is.")
    public boolean deleteRecord(@PathVariable @Valid String ediid) throws CustomizationException {
	logger.info("Delete the record from stagging given by ediid " + ediid);
	return uRepo.delete(ediid);
    }

    /**
     * Finalize changes made in the record and send it back to bakend metadata
     * server to merge and send for review.
     * 
     * @param ediid  Unique record id
     * @param params Modified fields in JSON
     * @return Updated JSON record
     * @throws CustomizationException
     * @throws InvalidInputException
     */
    @RequestMapping(value = {
	    "savedrecord/{ediid}" }, method = RequestMethod.PUT, headers = "accept=application/json", produces = "application/json")
    @ApiOperation(value = ".", nickname = "Save changes to server", notes = "Resource returns a boolean based on success or failure of the request.")
    public Document saveRecord(@PathVariable @Valid String ediid, @Valid @RequestBody String params)
	    throws CustomizationException, InvalidInputException, ResourceNotFoundException {
	logger.info("Send updated record to backend metadata server:" + ediid);
	return uRepo.save(ediid, params);

    }

    @ExceptionHandler(CustomizationException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorInfo handleCustomization(CustomizationException ex, HttpServletRequest req) {
	logger.error("There is an error in the service: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
	return new ErrorInfo(req.getRequestURI(), 500, "Internal Server Error");
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorInfo handleStreamingError(ResourceNotFoundException ex, HttpServletRequest req) {
	logger.info("There is an error accessing requested record : " + req.getRequestURI() + "\n  " + ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 404, "Resource Not Found", req.getMethod());
    }

    @ExceptionHandler(InvalidInputException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorInfo handleStreamingError(InvalidInputException ex, HttpServletRequest req) {
	logger.info("There is an error processing input data: " + req.getRequestURI() + "\n  " + ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 400, "Invalid input error", "PATCH");
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

    @ExceptionHandler(RestClientException.class)
    @ResponseStatus(HttpStatus.BAD_GATEWAY)
    public ErrorInfo handleRestClientError(RuntimeException ex, HttpServletRequest req) {
	logger.error("Unexpected failure during request: " + req.getRequestURI() + "\n  " + ex.getMessage(), ex);
	return new ErrorInfo(req.getRequestURI(), 502, "Can not connect to backend server");
    }
}
