package gov.nist.oar.customizationapi.web;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.view.RedirectView;

import io.swagger.annotations.Api;

/**
 * This controller is added for testing the api locally without having to connect to external identity provider.
 * @author Deoyani S Nandrekar-Heinis
 *
 */
@RestController
@Validated
@CrossOrigin(origins = "*", allowedHeaders = "*")
@RequestMapping("/saml/login")
@Profile({"local"})
public class LocalSamlController {
	private Logger logger = LoggerFactory.getLogger(LocalSamlController.class);
	
	@RequestMapping( method = RequestMethod.GET)
	public RedirectView redirect(@RequestParam String redirectTo) {
		System.out.print("test:"+redirectTo);
		logger.info("This should be called only while running locally. This authenticates all the requests.");
		return new RedirectView(redirectTo);
	}

}
