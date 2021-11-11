package gov.nist.oar.customizationapi;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
/***
 * The class is an entry point for an application to start running on server.
 * @author Deoyani Nandrekar-Heinis
 */
@SpringBootApplication(exclude={SecurityAutoConfiguration.class})
@RefreshScope
@ComponentScan(basePackages = { "gov.nist.oar.customizationapi" })
//@EnableAutoConfiguration(exclude = { MongoAutoConfiguration.class })
public class CustomizationApiApplication {

	public static void main(String[] args) {
		System.out.println("********* Starting Customization Service **********");
		SpringApplication.run(CustomizationApiApplication.class, args);
	}

	@Bean
    public OpenAPI customOpenAPI(@Value("1.1.0") String appVersion) {
	appVersion = VERSION;
	List<Server> servers = new ArrayList<>();
	servers.add(new Server().url("/customization"));
	String description = "These are set of APIs which are used by data publishing workflow to edit new dataset metadata records.";
		
	
       return new OpenAPI()
        .components(new Components().addSecuritySchemes("basicScheme",
                new SecurityScheme().type(SecurityScheme.Type.HTTP).scheme("basic")))
	       .components(new Components()).servers(servers)
        .info(new Info().title("Metadata Cutomization API")
                .description(description)
                .version(appVersion)
                
                .license(new License().name("NIST Software").url("https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications")));
    }
    
    /**
     * The service name
     */
    public final static String NAME;

    /**
     * The version of the service
     */
    public final static String VERSION;

    static {
        String name = null;
        String version = null;
        try (InputStream verf =  CustomizationApiApplication.class.getClassLoader().getResourceAsStream("VERSION")) {
            if (verf == null) {
                name = "oar-customization";
                version = "not set";
            }
            else {
                BufferedReader vrdr = new BufferedReader(new InputStreamReader(verf));
                String line = vrdr.readLine();
                String[] parts = line.split("\\s+");
                name = parts[0];
                version = (parts.length > 1) ? parts[1] : "missing";
            }
        } catch (Exception ex) {
            name = "oar-customization";
            version = "unknown";
        }
        NAME = name;
        VERSION = version;
    }
}