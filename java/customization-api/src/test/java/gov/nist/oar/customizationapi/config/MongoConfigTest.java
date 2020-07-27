package gov.nist.oar.customizationapi.config;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = MongoConfig.class)
@TestPropertySource(locations = "classpath:testapp.yml")
public class MongoConfigTest {

	@Autowired
	MongoConfig mongoConfig;

	@Value("${oar.mongodb.host:localhost}")
	private String host;

	@Value("${oar.mongodb.database.name:UpdateDB}")
	private String dbname;

	@Test
	public void mongoConfigTest() {
		System.out.println("Test:" + host);
		assertEquals(mongoConfig.getMetadataServer(), "\"http://mdserver:8081/\"");
		assertEquals(mongoConfig.getMDSecret(), "\"testsecret\"");
		assertEquals(host, "someserver");
		assertEquals(dbname, "somedb");

	}

}