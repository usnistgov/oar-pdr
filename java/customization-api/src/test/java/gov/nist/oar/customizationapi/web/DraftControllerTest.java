

package gov.nist.oar.customizationapi.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

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
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import gov.nist.oar.customizationapi.repositories.UpdateRepository;

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
	UpdateRepository updateRepo;

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

	}

	@Test
	public void editRecordTest() throws Exception {
		String ediid = "12345";

		Mockito.doReturn(record).when(updateRepo).getRecord(ediid);

		MockHttpServletResponse response = mvc.perform(get("/pdr/lp/draft/" + ediid).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		System.out.println("Output::" + response.getContentAsString());

		assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());

	}

	@Test
	public void deleteRecordTest() throws Exception {
		String ediid = "12345";

		Mockito.doReturn(false).when(updateRepo).delete(ediid);

		MockHttpServletResponse response = mvc.perform(delete("/pdr/lp/draft/" + ediid).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		assertThat(response.getStatus()).isEqualTo(HttpStatus.OK.value());
		assertThat(response.getContentAsString()).isEqualTo("false");

	}

	@Test
	public void putRecordTest() throws Exception {
		String ediid = "12345";

		Mockito.doReturn(true).when(updateRepo).put(ediid, changedata);

		MockHttpServletResponse response = mvc
				.perform(put("/pdr/lp/draft/" + ediid).content(changedata).accept(MediaType.APPLICATION_JSON))
				.andReturn().getResponse();

		//Document responseDoc = Document.parse(response.getContentAsString());

//		String title = "New Title Update Test May 14";
		//assertThat(title).isEqualTo(responseDoc.get("title"));

		assertThat(response.getStatus()).isEqualTo(HttpStatus.CREATED.value());

	}

	

}
