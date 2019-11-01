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
import java.util.List;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import gov.nist.oar.custom.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.custom.customizationapi.exceptions.ErrorInfo;
import gov.nist.oar.custom.customizationapi.exceptions.UnAuthenticatedUserException;
import gov.nist.oar.custom.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.custom.customizationapi.helpers.domains.UserToken;
import gov.nist.oar.custom.customizationapi.service.JWTTokenGenerator;
import gov.nist.oar.custom.customizationapi.service.ResourceNotFoundException;
import io.swagger.annotations.ApiOperation;

/**
 * This controller sends JWT, a token generated after successful authentication.
 * This token can be used to further communicated with service.
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@RestController
@RequestMapping("/auth")
public class AuthController {

    private Logger logger = LoggerFactory.getLogger(AuthController.class);

    @Autowired
    JWTTokenGenerator jwt;

    /**
     * Get the JWT for the authorized user
     * 
     * @param authentication
     * @param ediid
     * @return JSON with userid and token
     * @throws UnAuthorizedUserException
     * @throws CustomizationException
     * @throws UnAuthenticatedUserException 
     */
    @RequestMapping(value = { "_perm/{ediid}" }, method = RequestMethod.GET, produces = "application/json")
    @ApiOperation(value = "", nickname = "Authorize user to edit the record", notes = "Resource returns a JSON if Authorized user.")

    public UserToken token(Authentication authentication, @PathVariable @Valid String ediid)
	    throws UnAuthorizedUserException, CustomizationException, UnAuthenticatedUserException {
	String userId = "";
	try {
	    if (authentication == null)
		throw new UnAuthenticatedUserException(" User is not authenticated to access this resource.");
	    logger.info("Get the token for authenticated user.");

	    SAMLCredential credential = (SAMLCredential) authentication.getCredentials();
	    List<Attribute> attributes = credential.getAttributes();

	    org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	    userId = xsImpl.getTextContent();

	    return jwt.getJWT(userId, ediid);
	} catch (UnAuthorizedUserException ex) {
	    if (!userId.isEmpty() && userId != null)
		return new UserToken(userId, "");
	    
	    else
		throw ex;
	}

    }

    /**
     * Get Authenticated user information
     * 
     * @param response
     * @return JSON user id
     * @throws IOException
     */

//    @GetMapping("/loginfo")
    @RequestMapping(value = { "/_logininfo" }, method = RequestMethod.GET, produces = "application/json")
    public ResponseEntity<String> login(HttpServletResponse response) throws IOException {
	logger.info("Get the authenticated user info.");
	final Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

	if (authentication == null) {
	    response.sendRedirect("/saml/login");
	} else {
	    SAMLCredential credential = (SAMLCredential) authentication.getCredentials();
	    List<Attribute> attributes = credential.getAttributes();
	    org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	    String userId = xsImpl.getTextContent();
	    String returnResponse = "{\"userid\": \"" + userId + "\"}";
	    return new ResponseEntity<>(returnResponse, HttpStatus.OK);
	}
	return null;
    }

    /**
     * Exception handling if resource not found
     * 
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
     * Exception handling if user is not authorized
     * 
     * @param ex
     * @param req
     * @return
     */
    @ExceptionHandler(UnAuthorizedUserException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorInfo handleStreamingError(UnAuthorizedUserException ex, HttpServletRequest req) {
	logger.info("There user requesting edit access is not authorized : " + req.getRequestURI() + "\n  "
		+ ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 401, "UnauthroizedUser", req.getMethod());
    }

    /**
     * Exception handling if user is not authorized
     * 
     * @param ex
     * @param req
     * @return
     */
    @ExceptionHandler(UnAuthenticatedUserException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorInfo handleStreamingError(UnAuthenticatedUserException ex, HttpServletRequest req) {
	logger.info("There user requesting edit access is not authorized : " + req.getRequestURI() + "\n  "
		+ ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 401, "UnAuthenticated", req.getMethod());
    }
    /**
     * When an exception occurs in the customization service while connecting
     * backend or for any other reason.
     * 
     * @param ex
     * @param req
     * @return
     */
    @ExceptionHandler(CustomizationException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorInfo handleStreamingError(CustomizationException ex, HttpServletRequest req) {
	logger.info("There is an internal error connecting to backend service: " + req.getRequestURI() + "\n  "
		+ ex.getMessage());
	return new ErrorInfo(req.getRequestURI(), 500, "Internal Server Error", "GET");
    }
}