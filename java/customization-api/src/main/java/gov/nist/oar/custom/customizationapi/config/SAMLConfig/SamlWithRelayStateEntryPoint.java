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
package gov.nist.oar.custom.customizationapi.config.SAMLConfig;

import org.springframework.security.core.AuthenticationException;
import org.springframework.security.saml.SAMLEntryPoint;
import org.springframework.security.saml.context.SAMLMessageContext;
import org.springframework.security.saml.websso.WebSSOProfileOptions;

/***
 * This helps SAML endpoint to redirect after successful login service.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class SamlWithRelayStateEntryPoint extends SAMLEntryPoint {

    public SamlWithRelayStateEntryPoint() {

    }

    private String relaystate = "";

    public SamlWithRelayStateEntryPoint(String connectingapp) {
	this.relaystate = connectingapp;
    }

    @Override
    protected WebSSOProfileOptions getProfileOptions(SAMLMessageContext context, AuthenticationException exception) {

	WebSSOProfileOptions ssoProfileOptions;
	if (defaultOptions != null) {
	    ssoProfileOptions = defaultOptions.clone();
	} else {
	    ssoProfileOptions = new WebSSOProfileOptions();
	}

//        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
//        if (!(authentication instanceof AnonymousAuthenticationToken)) {
//            String currentUserName = authentication.getName();
//            System.out.println("****** TEST ***** +"+currentUserName);
//        }
//        System.out.println("****** TEST ***** +"+context);

	// Not :
	// Add your custom logic here if you need it.
	// Original HttpRequest can be extracted from the context param
	// So you can let the caller pass you some special param which can be used to
	// build an on-the-fly custom
	// relay state param

	// ssoProfileOptions.setRelayState("http://localhost:4200");
	ssoProfileOptions.setRelayState(this.relaystate);
//        ssoProfileOptions.setRelayState("https://inet.nist.gov/");
	return ssoProfileOptions;
    }

}