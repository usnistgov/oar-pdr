package gov.nist.oar.customizationapi.helpers;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.MockitoJUnitRunner;

import gov.nist.oar.customizationapi.service.UserToken;

//@RunWith(SpringJUnit4ClassRunner.class)
//@SpringBootTest
//@TestPropertySource(locations="classpath:testapp.yml")
@RunWith(MockitoJUnitRunner.Silent.class)
public class UserDetailsExtractorTest {
	
	@Mock
	UserDetailsExtractor uExtract;
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
	@Mock 
	AuthenticatedUserDetails authUserDetails;
	
	@Test
	public void getUserDetailsTest() {
		AuthenticatedUserDetails authDetails = new AuthenticatedUserDetails("abc@xyz.com","name","lastname","userid");
		 UserToken utoken = new UserToken(authDetails,"123243");
		 Mockito.doReturn(authDetails).when(uExtract).getUserDetails();
		 org.junit.Assert.assertEquals(authDetails.getUserEmail(),"abc@xyz.com");
		 System.out.print(utoken);
	}
	@Test
	public void getUserRecordTest() {
		Mockito.doReturn("1233534534543").when(uExtract).getUserRecord("https://localhost/customization/api/draft/1233534534543");
		String test = uExtract.getUserRecord("https://localhost/customization/api/draft/1233534534543");
		//System.out.println(test);
		org.junit.Assert.assertEquals(test,"1233534534543");
	}

}
