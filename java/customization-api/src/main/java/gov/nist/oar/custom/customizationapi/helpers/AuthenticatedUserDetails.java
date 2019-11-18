package gov.nist.oar.custom.customizationapi.helpers;

import java.io.Serializable;

public class AuthenticatedUserDetails implements Serializable {

    /**
     * 
     */
    private static final long serialVersionUID = 2968533695286307068L;
    private String userId;
    private String userName;
    private String userLastName;
    private String userEmail;

    public AuthenticatedUserDetails( ) {}
    public AuthenticatedUserDetails( String userEmail, String userName, String userLastName,String userId) {
	this.userId = userId;
	this.userName = userName;
	this.userLastName = userLastName;
	this.userEmail = userEmail;
    }

    public void setUserId(String userId) {
	this.userId = userId;
    }

    public void setUserName(String userName) {
	this.userName = userName;
    }

    public void setUserLastName(String userLastName) {
	this.userLastName = userLastName;
    }

    public void setUserEmail(String userEmail) {
	this.userEmail = userEmail;
    }

    public String getUserId() {
	return this.userId;
    }

    public String getUserName() {
	return this.userName;
    }

    public String getUserLastName() {
	return this.userLastName;
    }

    public String getUserEmail() {
	return this.userEmail;
    }

}
