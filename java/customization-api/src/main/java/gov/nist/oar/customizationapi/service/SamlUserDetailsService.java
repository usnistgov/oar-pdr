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
package gov.nist.oar.customizationapi.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.security.saml.userdetails.SAMLUserDetailsService;

import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;

/**
 * This service is called by SAML authentication provider.
 * @author Deoyani Nandrekar-Heinis
 */
public class SamlUserDetailsService implements SAMLUserDetailsService {

	@Value("${saml.nist.attribute.claim.email}")
	private String email;

	@Value("${saml.nist.attribute.claim.lastname}")
	private String lastname;

	@Value("${saml.nist.attribute.claim.name}")
	private String name;

	@Value("${saml.nist.attribute.claim.userid}")
	private String userid;

	@Override
	public Object loadUserBySAML(SAMLCredential credential) throws UsernameNotFoundException {
		String userEmail1 = credential.getAttributeAsString(email);
		System.out.println("userEmail1:" + userEmail1);
		AuthenticatedUserDetails samUser = new AuthenticatedUserDetails(credential.getAttributeAsString(email),
				credential.getAttributeAsString(name), credential.getAttributeAsString(lastname),
				credential.getAttributeAsString(userid));
		return samUser;
	}
}