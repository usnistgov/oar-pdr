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

import java.io.Serializable;

import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;

/**
 * This class is to store user id and JWT information for authorized user.
 * It also has field to represent error message in case user is authenticated 
 * but authorization process generates some error and no token is generated.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class UserToken implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = -3414986086109823716L;
	private String token;
	private AuthenticatedUserDetails userDetails;
	private String errorMessage;

	public UserToken(AuthenticatedUserDetails userDetails, String token, String errorMessage) {
		this.token = token;
		this.userDetails = userDetails;
		this.errorMessage = errorMessage;
	}

	/**
	 * get the JWT generated for authorized user
	 * @return String
	 */
	public String getToken() {
		return token;
	}

	/**
	 * Set the JWT generated for authorized user
	 * @param token
	 */
	public void setToken(String token) {
		this.token = token;
	}
	/**
	 * Get authenticated user details
	 * @return
	 */
	public AuthenticatedUserDetails getUserDetails() {
		return this.userDetails;
	}

	/**
	 * Set authenticated user details
	 * @param userDetails
	 */
	public void setUserDetails(AuthenticatedUserDetails userDetails) {
		this.userDetails = userDetails;
	}
	
	/***
	 * Set this error message if there is an error while token is generated 
	 * for example due to back end authorization service response.
	 * @param errorMessage
	 */
	public void setErrorMessage(String errorMessage) {
		this.errorMessage = errorMessage;
	}
	
	/***
	 * Get any error message associated with the user while authorizing user and no token is generated.
	 * @return
	 */
	public String getErrorMessage() {
		return this.errorMessage;
	}
}