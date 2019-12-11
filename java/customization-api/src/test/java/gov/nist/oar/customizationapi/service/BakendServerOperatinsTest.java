package gov.nist.oar.customizationapi.service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.junit.runner.RunWith;
import org.mockito.Matchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.runners.MockitoJUnitRunner;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;

import org.bson.Document;

@RunWith(MockitoJUnitRunner.class)
public class BakendServerOperatinsTest {
	String mdserver = "http://localhost";
	String mdsecret = "mdsecret";

	@Mock
	private RestTemplate restTemplate;
//	 @Test
//	    public void testXXX() throws Exception {
////	        Mockito.when(this.restTemplate.exchange(Matchers.anyString(), Matchers.any(HttpMethod.class), Matchers.any(), Matchers.<Class<String>>any(), Matchers.<Object>anyVararg()))
////	               .thenReturn(ResponseEntity.ok("foo"));
//
//	        Mockito.when(this.restTemplate.getForObject(Matchers.anyString(), Matchers.any(), Matchers.<Class<String>>any(), Matchers.<Object>anyVararg()))
//            .thenReturn(ResponseEntity.ok("foo"));
//	        final Bar bar = new Bar(this.restTemplate);
//	        assertThat(bar.foobar()).isEqualTo("foo");
//	    }
//
//	    class Bar {
//	        private final RestTemplate restTemplate;
//
//	        Bar(final RestTemplate restTemplate) {
//	            this.restTemplate = restTemplate;
//	        }
//
//	        public String foobar() {
//	            final ResponseEntity<String> exchange = this.restTemplate.exchange("ffi", HttpMethod.GET, HttpEntity.EMPTY, String.class, 1, 2, 3);
//	            return exchange.getBody();
//	        }
//	    }

//	 @Before
//	    public void prepare() throws IOException {
//		 String recorddata = new String ( Files.readAllBytes( 
//			       Paths.get(
//				       this.getClass().getClassLoader().getResource("record.json").getFile())));
//	        ResponseEntity<String> response = new ResponseEntity<>(recorddata, HttpStatus.OK);
////	     Mockito.doReturn(response).when(restTemplate.getForEntity(Mockito.anyString(), String.class));
//		 Document recordDoc = Document.parse(recorddata);
////		 Mockito.doReturn(recordDoc).when(restTemplate.getForObject(mdserver + "123253425", Document.class));
////		 Mockito.when(this.restTemplate.getForObject(Matchers.anyString(), Matchers.any(), Matchers.<Class<String>>any(), Matchers.<Object>anyVararg()))
////         .thenReturn(ResponseEntity.ok(recordDoc));
//		 Mockito.doReturn(ResponseEntity.ok(recordDoc)).when(this.restTemplate).getForObject(Matchers.anyString(), Matchers.any(), Matchers.<Class<String>>any(), Matchers.<Object>anyVararg());
//	 }
	@Test
	public void getDataFromServerTest() throws IOException {
		String recorddata = new String(
				Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("record.json").getFile())));
		ResponseEntity<String> response = new ResponseEntity<>(recorddata, HttpStatus.OK);
		Document recordDoc = Document.parse(recorddata);
		Mockito.doReturn(recordDoc).when(this.restTemplate).getForObject(Matchers.anyString(),
				Matchers.any());

		BackendServerOperations backendServerOps = new BackendServerOperations(this.restTemplate);
		Document d = backendServerOps.getDataFromServer(mdserver, "123253425");
		String title = "New Title Update Test May 7";
		assertEquals(title, d.getString("title"));
		System.out.print("Doc:" + d.getString("title"));
	}
}
