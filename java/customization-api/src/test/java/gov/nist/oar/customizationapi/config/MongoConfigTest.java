package gov.nist.oar.customizationapi.config;


import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

//import gov.nist.oar.customizationapi.config.MongoConfig;


@RunWith(SpringJUnit4ClassRunner.class)
//@ContextConfiguration(classes = MongoConfig.class)
@TestPropertySource(locations="classpath:testapp.yml")
public class MongoConfigTest {
	
//	 @Autowired
//	 MongoConfig mongoConfig;
//
//	@Test
//	public void mongoConfigTest() {
//		assertEquals(mongoConfig.getMetadataServer(), "http://mdserver:8081/");
//	}
	
}