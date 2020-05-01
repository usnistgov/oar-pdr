package gov.nist.oar.customizationapi.web;

import javax.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.UnAuthenticatedUserException;
import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
import gov.nist.oar.customizationapi.service.UserToken;

/**
 * This controller is added for testing the api locally without having to connect to authorization service.
 * @author Deoyani S Nandrekar-Heinis
 *
 */
@RestController
@CrossOrigin(origins = "*", allowedHeaders = "*")
@RequestMapping("/auth")
@Profile({ "local" })
public class LocalAuthController {
	private Logger logger = LoggerFactory.getLogger(LocalAuthController.class);

	@RequestMapping(value = { "_perm/{ediid}" }, method = RequestMethod.GET, produces = "application/json")
	public UserToken token(Authentication authentication, @PathVariable @Valid String ediid)
			throws UnAuthorizedUserException, CustomizationException, UnAuthenticatedUserException, BadGetwayException {
		logger.info("This should be called only in local profile, while testing locally. It returns sample user values.");
		return new UserToken(new AuthenticatedUserDetails("TestGuest@nist.gov", "Guest", "User", "Guest"),
				"L$c#aL%t@S!", "");
	}
}
