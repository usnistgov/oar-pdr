package gov.nist.oar.customizationapi.service;

import org.junit.Rule;

//import static org.mockito.Mockito.spy;
//import static org.mockito.Mockito.when;

import org.junit.Test;
import org.junit.rules.ExpectedException;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.Mockito;

import static org.junit.Assert.assertEquals;
import static org.mockito.ArgumentMatchers.*;


//import org.powermock.api.mockito.PowerMockito;
//import org.powermock.core.classloader.annotations.PowerMockIgnore;
//import org.powermock.modules.junit4.PowerMockRunner;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;

////@PowerMockIgnore({"com.sun.org.apache.xerces.*", "javax.xml.*", "org.xml.*", "org.w3c.*", "com.sun.org.apache.xalan.*"})
//@PowerMockIgnore({"javax.management.", "com.sun.org.apache.xerces.", "javax.xml.", "org.xml.", "org.w3c.dom.",
//"com.sun.org.apache.xalan.", "javax.activation.*"})
//@RunWith(PowerMockRunner.class)
public class JWTTokenGeneratorTest {

	private Logger logger = LoggerFactory.getLogger(JWTTokenGeneratorTest.class);

	private String mdsecret = "testsecret";

	private String mdserver = "testserver";

	private String JWTClaimName = "testName";

	private String JWTClaimValue = "testvalue";

//	private String JWTSECRET = "jwtsecret";
	
//	private String userToken = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tfDEyNDM1NjIxNDUzMTIiLCJleHAiOjE1NzYwMTMxODgsInRlc3ROYW1lIjoidGVzdHZhbHVlIn0.pul3GQJ6qk64v7YGsTKkQDolwLFRCl_qdvqnnD6vaOI\n" + 
//			"";
	
	 @Rule
	 public final ExpectedException exception = ExpectedException.none();

//
//	@Mock
//	private RestTemplate restTemplate;


	@Test
	public void testGetTokenSuccess() throws CustomizationException, UnAuthorizedUserException, BadGetwayException {
		final JWTTokenGenerator jwtGenerator = Mockito.spy( new JWTTokenGenerator());
		ReflectionTestUtils.setField(jwtGenerator, "mdsecret", mdsecret);
		ReflectionTestUtils.setField(jwtGenerator, "mdserver", mdserver);
		ReflectionTestUtils.setField(jwtGenerator, "JWTClaimName", JWTClaimName);
		ReflectionTestUtils.setField(jwtGenerator, "JWTClaimValue", JWTClaimValue);
		String newSecret = "yeWAgVDfb$!MFn@MCJVN7uqkznHbDLR#";
		ReflectionTestUtils.setField(jwtGenerator, "JWTSECRET", newSecret);
		AuthenticatedUserDetails authUserDetails = new AuthenticatedUserDetails("test@test.com", "testName",
				"testLastNAme", "testid");
		String ediid = "1243562145312";
		Mockito.doReturn(true).when(jwtGenerator).isAuthorized(authUserDetails, ediid);
		UserToken utoken = jwtGenerator.getJWT(authUserDetails, ediid);
		System.out.println(utoken.getToken());
//		assertEquals(utoken, userToken);
	}

	@Test
	public void testTokenFailure() throws UnAuthorizedUserException, BadGetwayException, CustomizationException {

		logger.info("Test to generate token");
		final JWTTokenGenerator jwtGenerator = Mockito.spy( new JWTTokenGenerator());
		ReflectionTestUtils.setField(jwtGenerator, "mdsecret", mdsecret);
		ReflectionTestUtils.setField(jwtGenerator, "mdserver", mdserver);
		ReflectionTestUtils.setField(jwtGenerator, "JWTClaimName", JWTClaimName);
		ReflectionTestUtils.setField(jwtGenerator, "JWTClaimValue", JWTClaimValue);
		ReflectionTestUtils.setField(jwtGenerator, "JWTSECRET", "hfgsdhfgsdf");

		AuthenticatedUserDetails authUserDetails = new AuthenticatedUserDetails("test@test.com", "testName",
				"testLastNAme", "testid");
		String ediid = "1243562145312";
		Mockito.doReturn(true).when(jwtGenerator).isAuthorized(authUserDetails, ediid);
		exception.expect(UnAuthorizedUserException.class);
		UserToken utoken = jwtGenerator.getJWT(authUserDetails, ediid);
		org.junit.Assert.assertNotNull(utoken);
//		System.out.println(utoken.getToken());

	}
//	@PowerMockIgnore({"com.sun.org.apache.xerces.*", "javax.xml.*", "org.xml.*", "org.w3c.*", "com.sun.org.apache.xalan.*"})
//	@Test
//	public void testIsAuthorized() throws Exception {
//		AuthenticatedUserDetails authUserDetails = new AuthenticatedUserDetails("test@test.com", "testName",
//				"testLastNAme", "testid");
//		String ediid = "1243562145312";
//		JWTTokenGenerator mock = PowerMockito.spy(new JWTTokenGenerator());
//		PowerMockito.doReturn(true).when(mock, "isAuthorized", authUserDetails, ediid);
//		System.out.print("test");
//	}
	
	@Test
	public void testIsAuthorized() throws Exception {
		AuthenticatedUserDetails authUserDetails = new AuthenticatedUserDetails("test@test.com", "testName",
				"testLastNAme", "testid");
		String ediid = "1243562145312";
		final JWTTokenGenerator jwtGenerator = Mockito.spy( new JWTTokenGenerator());
//		doReturn()
		Mockito.doReturn(true).when(jwtGenerator).isAuthorized(authUserDetails, ediid);
//		Mockito.when(jwtGenerator.isAuthorized(authUserDetails, ediid)).thenReturn(true);

	}
}
