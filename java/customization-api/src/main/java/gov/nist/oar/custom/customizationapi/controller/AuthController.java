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
package gov.nist.oar.custom.customizationapi.controller;



import java.util.List;

import org.joda.time.DateTime;
import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.springframework.security.core.Authentication;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import gov.nist.oar.custom.customizationapi.config.SAMLConfig.SecurityConstant;
import gov.nist.oar.custom.customizationapi.helpers.domains.UserToken;

/**
 * This controller sends JWT, a token generated after successful authentication.
 * This token can be used to further communicated with service.
 * @author  Deoyani Nandrekar-Heinis
 */
@RestController
//@CrossOrigin("http://localhost:4200")
@RequestMapping("/auth")
public class AuthController {

    @GetMapping("/token")
    public UserToken token(Authentication authentication) throws JOSEException {

        final DateTime dateTime = DateTime.now();
        //build claims

        JWTClaimsSet.Builder jwtClaimsSetBuilder = new JWTClaimsSet.Builder();
        jwtClaimsSetBuilder.expirationTime(dateTime.plusMinutes(120).toDate());
        jwtClaimsSetBuilder.claim("APP", "SAMPLE");

        //signature
        SignedJWT signedJWT = new SignedJWT(new JWSHeader(JWSAlgorithm.HS256), jwtClaimsSetBuilder.build());
        signedJWT.sign(new MACSigner(SecurityConstant.JWT_SECRET));

        SAMLCredential credential = (SAMLCredential) authentication.getCredentials();
	List<Attribute> attributes = credential.getAttributes();
	//XMLObjectChildrenList<Attribute>  
	org.opensaml.xml.schema.impl.XSAnyImpl xsImpl = (XSAnyImpl) attributes.get(0).getAttributeValues().get(0);
	String userId = xsImpl.getTextContent();
	
        return new UserToken(userId, signedJWT.serialize());
    }
    
}