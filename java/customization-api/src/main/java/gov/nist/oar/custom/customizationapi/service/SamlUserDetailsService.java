package gov.nist.oar.custom.customizationapi.service;

import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.security.saml.userdetails.SAMLUserDetailsService;

import gov.nist.oar.custom.customizationapi.helpers.domains.SamlUserDetails;

/**
 * @author
 */
public class SamlUserDetailsService implements SAMLUserDetailsService {

    @Override
    public Object loadUserBySAML(SAMLCredential credential) throws UsernameNotFoundException {
	final String userEmail = credential.getAttributeAsString("email");
	System.out.println("userEmail:" + userEmail);
	return new SamlUserDetails();
    }
}