package gov.nist.oar.custom.customizationapi.config.JWTConfig;

import java.io.IOException;
import java.text.ParseException;
import java.util.List;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.simple.JSONObject;
import org.opensaml.saml2.core.Attribute;
import org.opensaml.xml.schema.impl.XSAnyImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;

import com.nimbusds.jose.JWSObject;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import gov.nist.oar.custom.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.custom.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.custom.customizationapi.helpers.domains.UserToken;

/**
 * This filter users JWT configuration and filters all the service requests
 * which need authenticated token exchange.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */

public class JWTAuthenticationFilter extends AbstractAuthenticationProcessingFilter {

    private static final Logger logger = LoggerFactory.getLogger(JWTAuthenticationFilter.class);
    public static final String Header_Authorization_Token = "Authorization";
    public UserDetailsExtractor uExtract = new UserDetailsExtractor();

    public JWTAuthenticationFilter(final String matcher, AuthenticationManager authenticationManager) {
	super(matcher);
	super.setAuthenticationManager(authenticationManager);
    }

    /**
     * Parse requested token to extract information
     */
    @Override
    public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
	    throws IOException, ServletException {

	logger.info("Attempt to check token and  authorized token validity");
	String token = request.getHeader(Header_Authorization_Token);
	if (token != null)
	    token = token.substring(7).trim();
	String userId = uExtract.getUserId();
	String recordId = uExtract.getUserRecord(request.getRequestURI());
	try {

	    SignedJWT signedJWTtest = SignedJWT.parse(token);
	    JWTClaimsSet claimsSet = JWTClaimsSet.parse(signedJWTtest.getPayload().toJSONObject());

	    String[] userRecordId = claimsSet.getSubject().split("\\|");

	    if (!(userId.equals(userRecordId[0]) && recordId.equals(userRecordId[1]))) {
		logger.error("Unauthorized user: Token does not contain the user id or record id specified.");
		
		unsuccessfulAuthentication(request, response, new BadCredentialsException("Unauthorized user: Token does not contain the user id or record id specified."));
	    }
	  
	} catch (ParseException e) {
	    // TODO Auto-generated catch block
	    //e.printStackTrace();
	    logger.error("Unauthorized user: Token can not be parsed successfully.");
	    unsuccessfulAuthentication(request, response, new BadCredentialsException("Unauthorized user: Token can not be parsed successfully."));
	    //throw new IOException("Unauthorized user: Token can not be parsed successfully.");
	}

	JWTAuthenticationToken jwtAuthenticationToken = new JWTAuthenticationToken(token);

	return getAuthenticationManager().authenticate(jwtAuthenticationToken);
    }

    /**
     * CAlled if attempted request with token is valid and user is authorized to perform the task
     */
    @Override
    protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain,
	    Authentication authResult) throws IOException, ServletException {
	logger.info("If token is authorized redirect to original request.");
	chain.doFilter(request, response);
    }
    
    
/**
 * Called if attempted request with token is not valid and user is not authorized to perform this task.
 */
    @Override
    protected void unsuccessfulAuthentication(HttpServletRequest request, HttpServletResponse response,
	    AuthenticationException failed) throws IOException, ServletException {
//        SecurityContextHolder.clearContext(); //this will remove authenticated user completely
	Authentication auth = SecurityContextHolder.getContext().getAuthentication();
	String userId = "";
	if (auth != null) {
	    userId = uExtract.getUserId();
	}
	logger.info("If token is not authorized send Unauthorized status.");
	response.setStatus(HttpStatus.UNAUTHORIZED.value());
	response.setContentType(MediaType.APPLICATION_JSON_VALUE);
	JSONObject jObject = new JSONObject();
	if (!userId.isEmpty()) {
	    jObject.put("userId", userId);
	    jObject.put("message", "User is not Authorized.");
	} else {
	    jObject.put("message", "User is not Authenticated.");
	}

	response.getWriter().write(jObject.toJSONString());
    }

}