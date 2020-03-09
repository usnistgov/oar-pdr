package gov.nist.oar.customizationapi.config.ServiceConfig;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Map;


import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;

public class ServiceAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
	public static final String Header_Authorization_Token = "Authorization";
//	public static final String Token_starter = "Bearer";

	String secret;

	public ServiceAuthenticationFilter(final String matcher, AuthenticationManager authenticationManager) {

		super(matcher);
		super.setAuthenticationManager(authenticationManager);
	}

	public ServiceAuthenticationFilter(final String matcher) {
		super(matcher);
	}

	@Override
	public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
			throws AuthenticationException, IOException, ServletException {

		
		logger.info("Attempt to check token and  authorized token validity"
				+ request.getHeader(Header_Authorization_Token) + "test :" + secret);
		String token = request.getHeader(Header_Authorization_Token);
		if (token != null)
//			token = token.replaceAll(Token_starter, "").trim();
		token = token.trim();
		if (token == null || !token.equalsIgnoreCase(secret)) {
			logger.error("Unauthorized service: Token is null or Not Valid.");
			this.unsuccessfulAuthentication(request, response, new BadCredentialsException(
					"Unauthorized service request: Null or Invalid toke provided with the request."));
			return null;
		}

		return getAuthenticationManager().authenticate(new ServiceAuthToken(token));
	}

	@Override
	protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain,
			Authentication authResult) throws IOException, ServletException {
		logger.info("If token is authorized redirect to original request.");
		chain.doFilter(request, response);
	}

	@Override
	protected void unsuccessfulAuthentication(HttpServletRequest request, HttpServletResponse response,
			AuthenticationException failed) throws IOException, ServletException {
		logger.info("Unsuccessful attempt to authorize this service request");
	
		response.setStatus(HttpStatus.UNAUTHORIZED.value());
		response.setContentType(MediaType.APPLICATION_JSON_VALUE);
	}

	public void setSecret(String secret) {
		this.secret = secret;
	}
}
