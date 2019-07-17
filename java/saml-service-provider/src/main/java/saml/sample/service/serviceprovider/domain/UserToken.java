package saml.sample.service.serviceprovider.domain;


import java.io.Serializable;

public class UserToken implements Serializable {

    /**
     * 
     */
    private static final long serialVersionUID = -5239606569957105176L;
    private String token;
    private String userId;

    public UserToken(String userId, String token) {
        this.token = token;
        this.userId = userId;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }
    
    public String getUserId() {
	return this.userId;
    }
    
    public void  setUserId(String userId) {
	this.userId = userId;
    }
}