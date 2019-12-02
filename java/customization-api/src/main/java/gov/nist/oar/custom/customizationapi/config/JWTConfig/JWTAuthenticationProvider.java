package gov.nist.oar.custom.customizationapi.config.JWTConfig;

import java.text.ParseException;
import java.time.LocalDateTime;
import java.time.ZoneId;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.AuthenticationCredentialsNotFoundException;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.CredentialsExpiredException;
import org.springframework.security.authentication.InternalAuthenticationServiceException;
import org.springframework.security.core.Authentication;
import org.springframework.util.Assert;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
/**
 * JWTAuthenticationProvider class helps generate JWT, token once the user is
 * authenticated by SAML identity provider.
 * 
 * @author Deoyani Nandrekar-Heinis
 */

public class JWTAuthenticationProvider implements AuthenticationProvider {

    private static final Logger log = LoggerFactory.getLogger(JWTAuthenticationProvider.class);
    public String secret;
    
    @Override
    public boolean supports(Class<?> authentication) {
	return JWTAuthenticationToken.class.isAssignableFrom(authentication);
    }

    /**
     * Constructors with JWT secret
     * @param secret
     */
    public JWTAuthenticationProvider(String secret) {
	this.secret = secret;
    }
    
    @Override
    public Authentication authenticate(Authentication authentication) {
	log.info("Authorizing the request for given token");

	Assert.notNull(authentication, "Authentication is missing");

	Assert.isInstanceOf(JWTAuthenticationToken.class, authentication,
		"This method only accepts JWTAuthenticationToken");

	String jwtToken = authentication.getName();

	if (authentication.getPrincipal() == null || jwtToken == null) {
	    throw new AuthenticationCredentialsNotFoundException("Authentication token is missing");
	}

	final SignedJWT signedJWT;
	try {
	    signedJWT = SignedJWT.parse(jwtToken);

	    boolean isVerified = signedJWT.verify(new MACVerifier(secret.getBytes()));

	    if (!isVerified) {
		log.info("Signed JWT is not verified.");
		throw new BadCredentialsException("Invalid token signature");
	    }

	    // Check if token is expired ?
	    LocalDateTime expirationTime = LocalDateTime
		    .ofInstant(signedJWT.getJWTClaimsSet().getExpirationTime().toInstant(), ZoneId.systemDefault());

	    /// Add code for Metadata service
	    System.out.println("Expiration time: "+ expirationTime);
	    if (LocalDateTime.now(ZoneId.systemDefault()).isAfter(expirationTime)) {
		throw new CredentialsExpiredException("Token expired");
	    }

	    return new JWTAuthenticationToken(signedJWT, null, null);

	} catch (ParseException e) {
	    throw new InternalAuthenticationServiceException("Unreadable token");
	} catch (JOSEException e) {
	    throw new InternalAuthenticationServiceException("Unreadable signature");
	}
    }
}