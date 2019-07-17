package saml.sample.service.serviceprovider.service;


import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.security.saml.userdetails.SAMLUserDetailsService;

import saml.sample.service.serviceprovider.domain.SamlUserDetails;

/**
 * @author 
 */
public class SamlUserDetailsService implements SAMLUserDetailsService {

    @Override
    public Object loadUserBySAML(SAMLCredential credential) throws UsernameNotFoundException {
	 final String userEmail = credential.getAttributeAsString("email");
	 System.out.println("userEmail:"+userEmail);
        return new SamlUserDetails();
    }
}