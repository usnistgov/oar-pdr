package gov.nist.oar.customizationapi.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

import java.lang.annotation.Retention;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.MockitoJUnitRunner;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.test.context.support.WithSecurityContext;
import org.springframework.security.test.context.support.WithSecurityContextFactory;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.nimbusds.jose.JOSEException;
//import com.nimbusds.jose.proc.SecurityContext;

import gov.nist.oar.customizationapi.exceptions.BadGetwayException;
import gov.nist.oar.customizationapi.exceptions.CustomizationException;
import gov.nist.oar.customizationapi.exceptions.UnAuthenticatedUserException;
import gov.nist.oar.customizationapi.exceptions.UnAuthorizedUserException;
import gov.nist.oar.customizationapi.helpers.AuthenticatedUserDetails;
import gov.nist.oar.customizationapi.helpers.UserDetailsExtractor;
import gov.nist.oar.customizationapi.service.JWTTokenGenerator;
import gov.nist.oar.customizationapi.service.UserToken;

@RunWith(MockitoJUnitRunner.Silent.class)
public class AuthControllerTest {

	Logger logger = LoggerFactory.getLogger(AuthControllerTest.class);

	private MockMvc mvc;

	@Mock
	JWTTokenGenerator jwt;

	@Mock
	UserDetailsExtractor uExtract;

	@InjectMocks
	AuthController authController;

	@Before
	public void setup() {
		mvc = MockMvcBuilders.standaloneSetup(authController).build();
	}

	@Test
	public void getToken() throws Exception {
		String ediid = "123243";
		AuthenticatedUserDetails authDetails = new AuthenticatedUserDetails("abc@xyz.com", "name", "lastname",
				"userid");
		UserToken utoken = new UserToken(authDetails, "123243", "");

		Mockito.doReturn(utoken).when(jwt).getJWT(authDetails, ediid);

		// when
		MockHttpServletResponse response = mvc.perform(get("/auth/_perm/" + ediid).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		// then
		assertThat(response.getStatus()).isEqualTo(HttpStatus.UNAUTHORIZED.value());

	}

	@Test
	public void getTokenTest() throws Exception {
		String ediid = "123243";
		AuthenticatedUserDetails authDetails = new AuthenticatedUserDetails("abc@xyz.com", "name", "lastname",
				"userid");
		UserToken utoken = new UserToken(authDetails, "123243", "");

		MockHttpServletResponse response = mvc.perform(get("/auth/_perm/" + ediid).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();
		System.out.println(response.getContentAsString());

	}

}

@WithSecurityContext(factory = WithMockCustomUserSecurityContextFactory.class)
@interface WithMockCustomUser {

	String username() default "testuser";

	String password() default "testpassword";
}

class WithMockCustomUserSecurityContextFactory implements WithSecurityContextFactory<WithMockCustomUser> {
	@Override
	public SecurityContext createSecurityContext(WithMockCustomUser customUser) {
		SecurityContext context = SecurityContextHolder.createEmptyContext();

		MockUserDetails principal = new MockUserDetails(customUser.username(), customUser.password());
		Authentication auth = new UsernamePasswordAuthenticationToken(principal, "password",
				principal.getAuthorities());
		context.setAuthentication(auth);
		return context;
	}
}