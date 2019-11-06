package gov.nist.oar.custom.customizationapi.helpers;

import java.util.List;

import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;

public class UserDetailsExtractor {

    private static final Logger logger = LoggerFactory.getLogger(UserDetailsExtractor.class);
    
    /**
     * Return userId if authenticated user and in context else return empty string if no user can be extracted.
     * @return String userId
     */
    public String getUserId() {
	try {
	Authentication auth = SecurityContextHolder.getContext().getAuthentication();
	SAMLCredential credential = (SAMLCredential) auth.getCredentials();
	List<Attribute> attributes = credential.getAttributes();
	org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	return xsImpl.getTextContent();
	} catch(Exception exp) {
	    logger.error("No user is authenticated and return empty userid");
	    return "";
	}
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
