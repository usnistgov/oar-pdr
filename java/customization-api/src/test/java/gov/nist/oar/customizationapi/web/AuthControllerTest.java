//package gov.nist.oar.customizationapi.web;
//
//import static org.assertj.core.api.Assertions.assertThat;
//import static org.mockito.BDDMockito.given;
//import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
//
//import java.lang.annotation.Retention;
//
//import org.junit.Assert;
//import org.junit.Before;
//import org.junit.Test;
//import org.junit.runner.RunWith;
//import org.mockito.InjectMocks;
//import org.mockito.Mock;
//import org.mockito.Mockito;
//import org.mockito.junit.MockitoJUnitRunner;
//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;
//import org.springframework.http.HttpStatus;
//import org.springframework.http.MediaType;
//import org.springframework.mock.web.MockHttpServletResponse;
//import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
//import org.springframework.security.core.Authentication;
//import org.springframework.security.core.context.SecurityContext;
//import org.springframework.security.core.context.SecurityContextHolder;
//import org.springframework.security.test.context.support.WithSecurityContext;
//import org.springframework.security.test.context.support.WithSecurityContextFactory;
//import org.springframework.test.web.servlet.MockMvc;
//import org.springframework.test.web.servlet.setup.MockMvcBuilders;
//
//import com.nimbusds.jose.JOSEException;
////import com.nimbusds.jose.proc.SecurityContext;
//
//import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
//import gov.nist.oar.customizationapi.exceptions.CustomizationException;
//import gov.nist.oar.customizationapi.exceptions.UnAuthenticatedUserException;
//import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
//import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
//import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
//import gov.nist.oar.customizationapi.service.JWTTokenGenerator;
//import gov.nist.oar.customizationapi.service.UserToken;
//
//@RunWith(MockitoJUnitRunner.Silent.class)
////
////@RunWith(SpringJUnit4ClassRunner.class)
////@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
////@TestPropertySource(locations="classpath:testapp.yml")
//public class AuthControllerTest {
//
//	 Logger logger = LoggerFactory.getLogger(AuthControllerTest.class);
//	 
//	 private MockMvc mvc;
//
//	 @Mock
//	 JWTTokenGenerator jwt;
//	 
//	 @Mock 
//	 UserDetailsExtractor uExtract;
//	 
//	 @InjectMocks
//	 AuthController authController;
//	 
//	 @Before
//	 public void setup() {
//		 mvc = MockMvcBuilders.standaloneSetup(authController).build();
//	 }
//	 
//	 
//	 @Test
//	    public void getToken() throws Exception {
//		 String ediid ="123243";
//		 AuthenticatedUserDetails authDetails = new AuthenticatedUserDetails("abc@xyz.com","name","lastname","userid");
//		 UserToken utoken = new UserToken(authDetails,"123243");
//	     
//	        Mockito.doReturn(utoken).when(jwt).getJWT(authDetails, ediid);
//
//	        // when
//	        MockHttpServletResponse response = mvc.perform(get("/auth/_perm/"+ediid).accept(MediaType.APPLICATION_JSON)).andReturn().getResponse();
//
//	        // then
//	        assertThat(response.getStatus()).isEqualTo(HttpStatus.UNAUTHORIZED.value());
//	    
//	    }
//	 
//	 @Test
//	    public void getTokenTest() throws Exception {
//		 String ediid ="123243";
//		 AuthenticatedUserDetails authDetails = new AuthenticatedUserDetails("abc@xyz.com","name","lastname","userid");
//		 UserToken utoken = new UserToken(authDetails,"123243");
////		 Mockito.doReturn(true).when(jwt).isAuthorized(authDetails, ediid);
////	     Mockito.doReturn(utoken).when(jwt).getJWT(authDetails, ediid);
//		 given(jwt.isAuthorized(authDetails, ediid)).willReturn(true);
//	     given(jwt.getJWT(authDetails, ediid)).willReturn(utoken);
//
//	        // when
//	        MockHttpServletResponse response = mvc.perform(get("/auth/_perm/"+ediid).accept(MediaType.APPLICATION_JSON)).andReturn().getResponse();
//	        System.out.println(response.getContentAsString());
//	        // then
////	        assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());
//	    
//	    }
////	 @WithMockSaml(samlAssertFile = "/saml-auth-assert.xml")
////     @Test
////     public void testAuthController() throws JOSEException, UnAuthorizedUserException, CustomizationException, UnAuthenticatedUserException, BadGetwayException {
////
////         //final AuthController authController = new AuthController();
////
////		 SecurityContext context = SecurityContextHolder.createEmptyContext();
////
////		    MockUserDetails principal =
////		        new MockUserDetails(customUser.username(), customUser.password());
////		    Authentication auth =
////		        new UsernamePasswordAuthenticationToken(principal, "password", principal.getAuthorities());
////		    context.setAuthentication(auth);
//////		 SecurityContext test = new WithMockCustomUserSecurityContextFactory().createSecurityContext((WithMockCustomUser) new MockUserDetails("testuser","testpassword"));
////         final UserToken apiToken = authController.token(context.getAuthentication(), "43422");
////
////         Assert.assertNotNull(apiToken);
////         Assert.assertTrue(apiToken.getToken().length() > 0);
////     }
////
////	    @LocalServerPort
////	    int port;
////
////		private String mdsecret = "testsecret";
////
////		private String mdserver = "testserver";
////
////		private String JWTClaimName = "testName";
////
////		private String JWTClaimValue = "testvalue";
////	    TestRestTemplate websvc = new TestRestTemplate();
////	    HttpHeaders headers = new HttpHeaders();
////	    @Autowired
////	    UserDetailsExtractor uExtract;
////	    @Before
////	    public void initMocks() throws CustomizationException, UnAuthorizedUserException, BadGetwayException {
////	    	SAMLCredential samlCredential = Mockito.mock(SAMLCredential.class);
////			Authentication authentication = Mockito.mock(Authentication.class);
////			SecurityContext securityContext = Mockito.mock(SecurityContext.class);
////			SecurityContextHolder.setContext(securityContext);
////		    Mockito.when(SecurityContextHolder.getContext().getAuthentication()).thenReturn(authentication);
////			Mockito.doReturn(samlCredential).when(authentication).getCredentials();
////			Mockito.when(samlCredential.getAttributeAsString("lastname")).thenReturn("lastName");
////			Mockito.when(samlCredential.getAttributeAsString("firstname")).thenReturn("firstName");
////			Mockito.when(samlCredential.getAttributeAsString("email")).thenReturn("abc@xyz.com");
////			Mockito.doReturn("abc").when(samlCredential).getAttributeAsString("userid");
////			AuthenticatedUserDetails authDetails  = uExtract.getUserDetails();
////			
////			final JWTTokenGenerator jwtGenerator = Mockito.spy( new JWTTokenGenerator());
////			ReflectionTestUtils.setField(jwtGenerator, "mdsecret", mdsecret);
////			ReflectionTestUtils.setField(jwtGenerator, "mdserver", mdserver);
////			ReflectionTestUtils.setField(jwtGenerator, "JWTClaimName", JWTClaimName);
////			ReflectionTestUtils.setField(jwtGenerator, "JWTClaimValue", JWTClaimValue);
////			String newSecret = "yeWAgVDfb$!MFn@MCJVN7uqkznHbDLR#";
////			ReflectionTestUtils.setField(jwtGenerator, "JWTSECRET", newSecret);
////			AuthenticatedUserDetails authUserDetails = new AuthenticatedUserDetails("test@test.com", "testName",
////					"testLastNAme", "testid");
////			String ediid = "1243562145312";
////			Mockito.doReturn(true).when(jwtGenerator).isAuthorized(authUserDetails, ediid);
////			UserToken utoken = jwtGenerator.getJWT(authUserDetails, ediid);
////	    }
////	    @Test
////	    public void testAuth() {
//////	    	HttpEntity<String> req = new HttpEntity<String>(null, headers);
//////	        ResponseEntity<UserToken> resp = websvc.exchange(getBaseURL() +
//////	                                                          "_perm/123434",
//////	                                                      HttpMethod.GET, req, UserToken.class);
//////	        logger.info("getToken(): token:\n  " + resp.getBody());
////	    }
////	    private String getBaseURL() {
////	        return "http://localhost:" + port + "/customization/auth/";
////	    }
//}
//
////@Retention(RetentionPolicy.RUNTIME)
//@WithSecurityContext(factory = WithMockCustomUserSecurityContextFactory.class)
// @interface WithMockCustomUser {
//
//    String username() default "testuser";
//
//    String password() default "testpassword";
//}
//class WithMockCustomUserSecurityContextFactory
//implements WithSecurityContextFactory<WithMockCustomUser> {
//@Override
//public SecurityContext createSecurityContext(WithMockCustomUser customUser) {
//    SecurityContext context = SecurityContextHolder.createEmptyContext();
//
//    MockUserDetails principal =
//        new MockUserDetails(customUser.username(), customUser.password());
//    Authentication auth =
//        new UsernamePasswordAuthenticationToken(principal, "password", principal.getAuthorities());
//    context.setAuthentication(auth);
//    return context;
//}
//}