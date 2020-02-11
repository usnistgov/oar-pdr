package gov.nist.oar.customizationapi.config.ServiceConfig;

import org.springframework.security.authentication.AuthenticationCredentialsNotFoundException;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.util.Assert;

public class ServiceAuthenticationProvider implements AuthenticationProvider {

	@Override
	public boolean supports(Class<?> authentication) {
		return ServiceAuthToken.class.isAssignableFrom(authentication);
	}

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {

		Assert.notNull(authentication, "Authentication is missing");
		// TODO Auto-generated method stub
		Assert.isInstanceOf(ServiceAuthToken.class, authentication, "This method only accepts ServiceAuthToken");

		String authToken = authentication.getName();

		if (authentication.getPrincipal() == null || authToken == null) {
			throw new AuthenticationCredentialsNotFoundException("Authentication token is missing");
		}
		return new ServiceAuthToken(authToken);
	}

}
