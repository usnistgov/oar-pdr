
package gov.nist.oar.customizationapi.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import javax.servlet.http.HttpServletRequest;

import org.bson.Document;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.MockitoJUnitRunner;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.web.header.Header;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import gov.nist.oar.customizationapi.repositories.DraftService;

@RunWith(MockitoJUnitRunner.Silent.class)
//@RunWith(SpringJUnit4ClassRunner.class)
//@SpringBootTest
//@TestPropertySource(locations="classpath:testapp.yml")
public class DraftControllerTest {

	Logger logger = LoggerFactory.getLogger(DraftControllerTest.class);

	private MockMvc mvc;
	String recorddata, changedata, updated;
	Document record, changes, updatedDoc;
	@Mock
	DraftService draft;

	@InjectMocks
	DraftController draftController;

	@Before
	public void setup() throws IOException {
		mvc = MockMvcBuilders.standaloneSetup(draftController).build();

		recorddata = new String(
				Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("record.json").getFile())));
		record = Document.parse(recorddata);

		changedata = new String(
				Files.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("changes.json").getFile())));

		updated = new String(Files
				.readAllBytes(Paths.get(this.getClass().getClassLoader().getResource("updatedRecord.json").getFile())));

		updatedDoc = Document.parse(updated);

		ReflectionTestUtils.setField(draftController, "authorization", "mysecret");

	}

	@Test
	public void editRecordTest() throws Exception {
		String ediid = "12345";

//		HttpHeaders mockHeader = Mockito.mock(HttpHeaders.class);
//		HttpServletRequest request = Mockito.mock(HttpServletRequest.class);
//		// define the headers you want to be returned
//		Map<String, String> headers = new HashMap<>();
//		//headers.put(null, "HTTP/1.1 200 OK");
//		headers.put("Authorization", "mysecret");
//
//		// create an Enumeration over the header keys
//		Iterator<String> iterator = headers.keySet().iterator();
//		Enumeration headerNames = new Enumeration<String>() {
//		    @Override
//		    public boolean hasMoreElements() {
//		        return iterator.hasNext();
//		    }
//
//		    @Override
//		    public String nextElement() {
//		        return iterator.next();
//		    }
//		};
//		
//		// create an Enumeration over the header keys
//		Iterator<String> it = headers.values().iterator();
//		Enumeration headerValues = new Enumeration<String>() {
//		    @Override
//		    public boolean hasMoreElements() {
//		        return it.hasNext();
//		    }
//
//		    @Override
//		    public String nextElement() {
//		        return it.next();
//		    }
//		};
//
//
//		// mock the returned value of request.getHeaderNames()
////		Mockito.when(request.getHeaderNames()).thenReturn(headerNames);
////		Mockito.when(request.getHeader("Authorization")).thenReturn("mysecret");
//		
//		System.out.println("demonstrate output of request.getHeaderNames()");
//		while (headerNames.hasMoreElements()) {
//		    System.out.println("header name: " + headerNames.nextElement());
//		}
//		

		Mockito.doReturn(record).when(draft).getDraft(ediid, "");

		HttpHeaders httpHeaders = new HttpHeaders();
		httpHeaders.add("Authorization", "mysecret");
		MockHttpServletResponse response = mvc
				.perform(get("/pdr/lp/draft/" + ediid).headers(httpHeaders).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		//System.out.println("Output::" + response.getContentAsString());
		Document responseDoc = Document.parse(response.getContentAsString());
		//System.out.println("response.getContentAsString() ::"+response.getContentAsString());
		String title = "New Title Update Test May 7";
		assertThat(title).isEqualTo(responseDoc.get("title"));
		assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());

	}

	@Test
	public void deleteRecordTest() throws Exception {
		String ediid = "12345";

		Mockito.doReturn(false).when(draft).deleteDraft(ediid);

		HttpHeaders httpHeaders = new HttpHeaders();
		httpHeaders.add("Authorization", "mysecret");
		MockHttpServletResponse response = mvc
				.perform(delete("/pdr/lp/draft/" + ediid).headers(httpHeaders).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());
		assertThat(response.getContentAsString()).isEqualTo("false");

	}

	@Test
	public void putRecordTest() throws Exception {
		String ediid = "12345";

		Mockito.doNothing().when(draft).putDraft(ediid, Document.parse(changedata));
		HttpHeaders httpHeaders = new HttpHeaders();
		httpHeaders.add("Authorization", "mysecret");
		MockHttpServletResponse response = mvc
				.perform(put("/pdr/lp/draft/" + ediid).contentType(MediaType.APPLICATION_JSON).content(changedata)
						.headers(httpHeaders).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		assertThat(response.getStatus()).isEqualTo(HttpStatus.CREATED.value());

	}

}
