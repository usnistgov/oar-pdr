package gov.nist.oar.customizationapi.helpers;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.saml.SAMLCredential;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

@RunWith(SpringJUnit4ClassRunner.class)
//@SpringBootTest
//@TestPropertySource(locations="classpath:testapp.yml")

public class UserDetailsExtractorTest {
	
//	@Autowired
//	UserDetailsExtractor uExtract;
//	@Test
//	public void getUserDetailsTest() {
//		SAMLCredential samlCredential = Mockito.mock(SAMLCredential.class);
//		Authentication authentication = Mockito.mock(Authentication.class);
//		SecurityContext securityContext = Mockito.mock(SecurityContext.class);
//		SecurityContextHolder.setContext(securityContext);
//	    Mockito.when(SecurityContextHolder.getContext().getAuthentication()).thenReturn(authentication);
//		Mockito.doReturn(samlCredential).when(authentication).getCredentials();
//		Mockito.when(samlCredential.getAttributeAsString("lastname")).thenReturn("lastName");
//		Mockito.when(samlCredential.getAttributeAsString("firstname")).thenReturn("firstName");
//		Mockito.when(samlCredential.getAttributeAsString("email")).thenReturn("abc@xyz.com");
//		Mockito.doReturn("abc").when(samlCredential).getAttributeAsString("userid");
//		//Mockito.when(samlCredential.getAttributeAsString("userid")).thenReturn("abc");
//		AuthenticatedUserDetails authDetails  = uExtract.getUserDetails();
//		System.out.println(authDetails.getUserName());
//		//org.junit.Assert.assertEquals("lastName", authDetails.getUserName());
//		
//	}
//	
//	@Test
//	public void getUserRecordTest() {
//		String test = uExtract.getUserRecord("https://localhost/customization/api/draft/1233534534543");
//		System.out.println(test);
//	}

	@Test
	public void testThis() {
		System.out.println("random test");
	}
}
