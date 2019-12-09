package gov.nist.oar.customizationapi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.ComponentScan;


@SpringBootApplication
@RefreshScope
@ComponentScan(basePackages = {"gov.nist.oar.custom.customizationapi"})
@EnableAutoConfiguration(exclude={MongoAutoConfiguration.class})
public class CustomizationApiApplication {

  public static void main(String[] args) {
	System.out.println("MAIN CLASS *******************");
	
	SpringApplication.run(CustomizationApiApplication.class, args);
  }

}