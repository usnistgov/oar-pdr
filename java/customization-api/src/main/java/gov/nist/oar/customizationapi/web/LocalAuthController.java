package gov.nist.oar.customizationapi.web;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.ErrorInfo;
import gov.nist.oar.customizationapi.exceptions.UnAuthenticatedUserException;
import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
import gov.nist.oar.customizationapi.service.JWTTokenGenerator;
import gov.nist.oar.customizationapi.service.UserToken;

/**
 * This controller is added for testing the api locally without having to
 * connect to authorization service.
 * 
 * @author Deoyani S Nandrekar-Heinis
 *
 */
@RestController
@CrossOrigin(origins = "*", allowedHeaders = "*")
@RequestMapping("/auth")
//@Profile({ "local" }) //This setting can be used to enable the feature based on certain profiles/platforms.
@ConditionalOnProperty(value = "samlauth.enabled", havingValue = "false", matchIfMissing = true)
public class LocalAuthController {
	private Logger logger = LoggerFactory.getLogger(LocalAuthController.class);

	@Autowired
	JWTTokenGenerator jwt;

	@RequestMapping(value = { "_perm/{ediid}" }, method = RequestMethod.GET, produces = "application/json")
	public UserToken token(Authentication authentication, @PathVariable @Valid String ediid)
			throws UnAuthorizedUserException, CustomizationException, UnAuthenticatedUserException, BadGetwayException {
		logger.info(
				"This should be called only in local profile, while testing locally. It returns sample user values.");
//		String name = authentication.getName();
//		Object ob = authentication.getDetails();
//		Authentication auth = SecurityContextHolder.getContext().getAuthentication();
		if(authentication == null)throw new UnAuthenticatedUserException("No user authenticated to complete this request.");
		AuthenticatedUserDetails pauth = (AuthenticatedUserDetails) authentication.getPrincipal();
		return jwt.getLocalJWT(pauth,ediid);
	// return jwt.getLocalJWT(new AuthenticatedUserDetails("TestGuest@nist.gov", "Guest", "User", "Guest"), ediid);

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
}
