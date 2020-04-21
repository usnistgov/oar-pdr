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

import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;

/**
 * This class checks authenticated user and by calling backend service checks
 * whether user is authorized to edit the records. If user is authorized
 * generate token.
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Component
public class JWTTokenGenerator {

	private Logger logger = LoggerFactory.getLogger(JWTTokenGenerator.class);
	@Value("${oar.mdserver.secret:testsecret}")
	private String mdsecret;

	@Value("${oar.mdserver:}")
	private String mdserver;

	@Value("${jwt.claimname:testsecret}")
	private String JWTClaimName;

	@Value("${jwt.claimvalue:}")
	private String JWTClaimValue;

	@Value("${jwt.secret:}")
	private String JWTSECRET;

	/**
	 * Get the UserToken if user is authorized to edit given record.
	 * 
	 * @param userId Authenticated user
	 * @param ediid  Record identifier
	 * @return UserToken, userid and token
	 * @throws UnAuthorizedUserException
	 * @throws CustomizationException
	 */
	public UserToken getJWT(AuthenticatedUserDetails userDetails, String ediid)
			throws UnAuthorizedUserException, BadGetwayException, CustomizationException {
		logger.info("Get authorized user token.");
		isAuthorized(userDetails, ediid);

		try {
			final DateTime dateTime = DateTime.now();
			// build claims
			JWTClaimsSet.Builder jwtClaimsSetBuilder = new JWTClaimsSet.Builder();
			jwtClaimsSetBuilder.expirationTime(dateTime.plusMinutes(120).toDate());
			jwtClaimsSetBuilder.claim(JWTClaimName, JWTClaimValue);
			jwtClaimsSetBuilder.subject(userDetails.getUserEmail() + "|" + ediid);

			// signature
			SignedJWT signedJWT = new SignedJWT(new JWSHeader(JWSAlgorithm.HS256), jwtClaimsSetBuilder.build());
			signedJWT.sign(new MACSigner(JWTSECRET));

			return new UserToken(userDetails, signedJWT.serialize());
		} catch (JOSEException e) {
			logger.error("Unable to generate token for the this user." + e.getMessage());
			throw new UnAuthorizedUserException("Unable to generate token for the this user.");
		}
	}

	/***
	 * Connect to back end metadata service to check whether authenticated user is
	 * authorized to edit the record.
	 * 
	 * @param userId authenticated userid
	 * @param ediid  Record identifier
	 * @return boolean true if the user is authorized.
	 * @throws CustomizationException
	 * @throws UnAuthorizedUserException
	 */
	public void isAuthorized(AuthenticatedUserDetails userDetails, String ediid)
			throws CustomizationException, UnAuthorizedUserException, BadGetwayException {
		logger.info("Connect to backend metadata server to get the information.");
		try {
			String uri = mdserver + ediid + "/_perm/update/" + userDetails.getUserId();
			RestTemplate restTemplate = new RestTemplate();
			HttpHeaders headers = new HttpHeaders();
			headers.add("Authorization", "Bearer " + mdsecret);
			HttpEntity<String> requestEntity = new HttpEntity<>(null, headers);
			ResponseEntity<String> result = restTemplate.exchange(uri, HttpMethod.GET, requestEntity, String.class);
		} catch (Exception ie) {
			logger.error("There is an exception thrown while connecting to mdserver for authorizing current user."+ie.getMessage());
			throw new UnAuthorizedUserException("User is not authorized to edit this record.");
		}
	}

}
