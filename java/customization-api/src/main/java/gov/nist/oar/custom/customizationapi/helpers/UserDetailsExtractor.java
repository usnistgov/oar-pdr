package gov.nist.oar.custom.customizationapi.helpers;

import java.util.List;

import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.stereotype.Component;

@Component
public class UserDetailsExtractor {

    private static final Logger logger = LoggerFactory.getLogger(UserDetailsExtractor.class);
    
    @Value("${saml.nist.attribute.claim.email}")
    private String emailAttribute;
    
    @Value("${saml.nist.attribute.claim.lastname}")
    private String lastnameAttribute;
    
    @Value("${saml.nist.attribute.claim.name}")
    private String nameAttribute;
    
    @Value("${saml.nist.attribute.claim.userid}")
    private String useridAttribute;
    /**
     * Return userId if authenticated user and in context else return empty string if no user can be extracted.
     * @return String userId
     */
    
    public AuthenticatedUserDetails getUserId() {
	AuthenticatedUserDetails authUser = new AuthenticatedUserDetails();
	try {
	Authentication auth = SecurityContextHolder.getContext().getAuthentication();
	SAMLCredential credential = (SAMLCredential) auth.getCredentials();
//	List<Attribute> attributes = credential.getAttributes();
//	String lastName = credential.getAttributeAsString("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname");
	String lastName = credential.getAttributeAsString(lastnameAttribute);
	String name = credential.getAttributeAsString(nameAttribute);
	String email = credential.getAttributeAsString(emailAttribute);
	String userid = credential.getAttributeAsString(useridAttribute);
	authUser = new AuthenticatedUserDetails(email,name,lastName,userid);
	
	//	for(int i=0; i< 4;i++) {
//	    org.opensaml.xml.schema.impl.XSAnyImpl xsImpltest = (XSAnyImpl) attributes.get(i).getAttributeValues().get(0);
//	    //System.out.println("User details "+i+" ::"+xsImpltest.getTextContent());
//	   
//	}
//	org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	
//	return xsImpl.getTextContent();

	} catch(Exception exp) {
	    logger.error("No user is authenticated and return empty userid");
//	    return "";
	    
	}
	return authUser;
    }

    /**
     * Parse requestURL and get the record id which is a path parameter
     * @param requestURI
     * @return String recordid
     */
    public String getUserRecord(String requestURI) {
	String recordId = "";
	try {
	    recordId = requestURI.split("/draft/")[1];
	} catch (ArrayIndexOutOfBoundsException exp) {
	    try {
		recordId = requestURI.split("/savedrecord/")[1];
	    } catch (Exception ex) {
		logger.error("No record id is extracted fro request URL so empty string is returned");
		recordId = "";
		
	    }
	}
	return recordId;
    } 
}
