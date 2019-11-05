package gov.nist.oar.custom.customizationapi.helpers;

import java.util.List;

import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;

public class ExtractUserId {

    public static String getUserId() {
	Authentication auth = SecurityContextHolder.getContext().getAuthentication();
	SAMLCredential credential = (SAMLCredential) auth.getCredentials();
	List<Attribute> attributes = credential.getAttributes();
	org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	return xsImpl.getTextContent();
    }

}
