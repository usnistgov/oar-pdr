package gov.nist.oar.customizationapi;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.junit4.SpringRunner;


@RunWith(SpringJUnit4ClassRunner.class)
@TestPropertySource(locations = "classpath:testapp.yml")

public class UpdateapiApplicationTests {

	@Test
	public void contextLoads() {
	    assertEquals(true, true);
	}

}
