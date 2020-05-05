package gov.nist.oar.customizationapi.config.JWTConfig;

import java.io.IOException;
import java.text.ParseException;
import java.util.HashMap;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.json.simple.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;

/**
 *This filter is created only for testing local profile, which is used for testing users without registering to the organization's identity service.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */

public class JWTAuthenticationFilterLocal extends AbstractAuthenticationProcessingFilter {

	private static final Logger logger = LoggerFactory.getLogger(JWTAuthenticationFilterLocal.class);

	public static final String Header_Authorization_Token = "Authorization";
	public static final String Token_starter = "Bearer";

	public JWTAuthenticationFilterLocal(final String matcher, AuthenticationManager authenticationManager) {
		super(matcher);
		super.setAuthenticationManager(authenticationManager);
	}

	/**
	 * Parse requested token to extract information
	 */
	@Override
	public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
			throws IOException, ServletException {

		logger.info("## This filter is created for local authentication/authorization testing. ## ");
		Authentication auth = SecurityContextHolder.getContext().getAuthentication();
		AuthenticatedUserDetails pauth = (AuthenticatedUserDetails) auth.getPrincipal();
		
		String token = request.getHeader(Header_Authorization_Token);
		if (token == null) {
			logger.error("Unauthorized user: Token is null.");
			this.unsuccessfulAuthentication(request, response,
					new BadCredentialsException("Unauthorized user: Token is not provided with this request."));
			return null;
		}

		token = token.replaceAll(Token_starter, "").trim();
		String userId = pauth.getUserEmail();
		//** Make sure to check this code whenever there are api endpoints changes.
		String recordId = getUserRecord(request.getRequestURI());
		try {

			SignedJWT signedJWTtest = SignedJWT.parse(token);
			JWTClaimsSet claimsSet = JWTClaimsSet.parse(signedJWTtest.getPayload().toJSONObject());

			String[] userRecordId = claimsSet.getSubject().split("\\|");

			if (!(userId.equals(userRecordId[0]) && recordId.equals(userRecordId[1]))) {
				logger.error("Unauthorized user: Token does not contain the user id or record id specified.");
				this.unsuccessfulAuthentication(request, response, new BadCredentialsException(
						"Unauthorized user: Token does not contain the user id or record id specified."));
				return null;
			}

		} catch (ParseException e) {
			logger.error("Unauthorized user: Token can not be parsed successfully.");
			this.unsuccessfulAuthentication(request, response,
					new BadCredentialsException("Unauthorized user: Token can not be parsed successfully."));
			return null;
		}

		JWTAuthenticationToken jwtAuthenticationToken = new JWTAuthenticationToken(token);

		return getAuthenticationManager().authenticate(jwtAuthenticationToken);
	}

	/**
	 * Called if attempted request with token is valid and user is authorized to
	 * perform the task
	 */
	@Override
	protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain,
			Authentication authResult) throws IOException, ServletException {
		logger.info("If token is authorized redirect to original request.");
		chain.doFilter(request, response);
	}

	/**
	 * Called if attempted request with token is not valid and user is not
	 * authorized to perform this task.
	 */
	@Override
	protected void unsuccessfulAuthentication(HttpServletRequest request, HttpServletResponse response,
			AuthenticationException failed) throws IOException, ServletException {
		Authentication auth = SecurityContextHolder.getContext().getAuthentication();
		AuthenticatedUserDetails userDetails = null;
		if (auth != null) {
			userDetails = (AuthenticatedUserDetails) auth.getPrincipal();
		}
		logger.info("If token is not authorized send Unauthorized status.");
		response.setStatus(HttpStatus.UNAUTHORIZED.value());
		response.setContentType(MediaType.APPLICATION_JSON_VALUE);

		HashMap<String, Object> responseObject = new HashMap<String, Object>();

		if (userDetails != null) {
			responseObject.put("userId", userDetails.getUserId());
			responseObject.put("message", "User is not Authorized.");
		} else {
			responseObject.put("message", "User is not Authenticated.");
		}
		JSONObject jObject = new JSONObject(responseObject);
		response.getWriter().write(jObject.toJSONString());
	}

	/**
	 * Testing locally, Parse requestURL and get the record id which is a path parameter
	 * 
	 * @param requestURI
	 * @return String recordid
	 */
	public String getUserRecord(String requestURI) {
		String recordId = "";
		try {
			recordId = requestURI.split("/editor/")[1];
		} catch (ArrayIndexOutOfBoundsException exp) {

			logger.error("No record id is extracted from request URL so empty string is returned");
			recordId = "";

		}
		return recordId;
	}

}