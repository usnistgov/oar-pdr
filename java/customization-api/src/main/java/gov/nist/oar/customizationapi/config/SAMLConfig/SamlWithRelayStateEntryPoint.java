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
package gov.nist.oar.customizationapi.config.SAMLConfig;

import java.net.MalformedURLException;
import java.net.URL;

import org.opensaml.ws.transport.http.HttpServletRequestAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.saml.SAMLEntryPoint;
import org.springframework.security.saml.context.SAMLMessageContext;
import org.springframework.security.saml.websso.WebSSOProfileOptions;

import gov.nist.oar.customizationapi.exceptions.CustomizationException;

/***
 * This helps SAML endpoint to redirect after successful login.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class SamlWithRelayStateEntryPoint extends SAMLEntryPoint {
	private static final Logger log = LoggerFactory.getLogger(SamlWithRelayStateEntryPoint.class);

	private String defaultRedirect;

	public SamlWithRelayStateEntryPoint(String applicationURL) {
		this.defaultRedirect = applicationURL;
	}

	@Override
	protected WebSSOProfileOptions getProfileOptions(SAMLMessageContext context, AuthenticationException exception) {

		WebSSOProfileOptions ssoProfileOptions;
		if (defaultOptions != null) {
			ssoProfileOptions = defaultOptions.clone();
		} else {
			ssoProfileOptions = new WebSSOProfileOptions();
		}

		// Note for customization :
		// Original HttpRequest can be extracted from the context param
		// caller can pass redirect url with the request so after successful processing
		// user can be redirected to the same page.
		// if redirect URL is not specified user will be redirected to default url.

		HttpServletRequestAdapter httpServletRequestAdapter = (HttpServletRequestAdapter) context
				.getInboundMessageTransport();

		String redirectURL = httpServletRequestAdapter.getParameterValue("redirectTo");
		String[] urls = defaultRedirect.split(",");
		try {

			for (String urlString : urls) {
				URL url = new URL(redirectURL);
				URL nUrl = new URL(urlString);

				if (redirectURL == null) {

					ssoProfileOptions.setRelayState(urls[0]);
					break;
				}
				if (redirectURL != null && !url.getHost().equalsIgnoreCase(nUrl.getHost())) {
					ssoProfileOptions.setRelayState(urls[0]);

//				return null;
				}
				if (redirectURL != null && url.getHost().equalsIgnoreCase(nUrl.getHost())) {

					log.info("Redirect user to +" + redirectURL);
					ssoProfileOptions.setRelayState(redirectURL);
					break;
				}
			}

		} catch (MalformedURLException e) {
			ssoProfileOptions.setRelayState(urls[0]);
		}

		return ssoProfileOptions;
	}

}