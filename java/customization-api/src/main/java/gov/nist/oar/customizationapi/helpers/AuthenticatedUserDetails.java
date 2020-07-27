package gov.nist.oar.customizationapi.helpers;

import java.io.Serializable;

/**
 * AuthenticatedUserDetails class presents details of the user authenticated by
 * syste, In this case, it represents short system userId, User's name, User's
 * last name, User's emailid
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class AuthenticatedUserDetails implements Serializable {

	/**
	 * Serial version generated for this serializable class
	 */
	private static final long serialVersionUID = 2968533695286307068L;
	/**
	 * Short system user id
	 */
	private String userId;
	/**
	 * User's First Name
	 */
	private String userName;
	/**
	 * User's Last Name
	 */
	private String userLastName;
	/**
	 * User's email id
	 */
	private String userEmail;

	public AuthenticatedUserDetails() {
	}

	public AuthenticatedUserDetails(String userEmail, String userName, String userLastName, String userId) {
		this.userId = userId;
		this.userName = userName;
		this.userLastName = userLastName;
		this.userEmail = userEmail;
	}

	/**
	 * Set the User Id
	 * 
	 * @param userId
	 */
	public void setUserId(String userId) {
		this.userId = userId;
	}

	/**
	 * Set the user's first name
	 * 
	 * @param userName
	 */
	public void setUserName(String userName) {
		this.userName = userName;
	}

	/**
	 * Set User's Last Name
	 * 
	 * @param userLastName
	 */
	public void setUserLastName(String userLastName) {
		this.userLastName = userLastName;
	}

	/**
	 * Set User's email
	 * 
	 * @param userEmail
	 */
	public void setUserEmail(String userEmail) {
		this.userEmail = userEmail;
	}

	/**
	 * Get User's short Id
	 * 
	 * @return
	 */
	public String getUserId() {
		return this.userId;
	}

	/**
	 * Get User's first name
	 * 
	 * @return
	 */
	public String getUserName() {
		return this.userName;
	}

	/**
	 * Get User's last name
	 * 
	 * @return
	 */
	public String getUserLastName() {
		return this.userLastName;
	}

	/**
	 * Get User's email
	 * 
	 * @return
	 */
	public String getUserEmail() {
		return this.userEmail;
	}

}
