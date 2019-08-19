package gov.nist.oar.custom.customizationapi;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.mongo.MongoAutoConfiguration;
//import org.springframework.context.annotation.Bean;
//import org.springframework.web.servlet.config.annotation.CorsRegistry;
//import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
//import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
//import org.springframework.cloud.context.config.annotation.RefreshScope;
//import org.springframework.context.annotation.ComponentScan;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
//@RefreshScope
//@ComponentScan(basePackages = {"gov.nist.oar.custom"})
@EnableAutoConfiguration(exclude={MongoAutoConfiguration.class})
public class CustomizationApiApplication {
    
//    @Value("${oar.mdserver}")
//    private String msg;
//    
    public static void main(String[] args) {
	System.out.println("MAIN CLASS *******************");
	
	SpringApplication.run(CustomizationApiApplication.class, args);
    }

   
    
////    @RefreshScope
//    @RestController
//    class MessageRestController {
//     
//	@Value("${oar.mdserver}")
//        private String msg;
//     
//        @RequestMapping("/msg")
//        String getMsg() {
//            return this.msg;
//        }
//    }

//    /**
//     * Add CORS
//     * 
//     * @return
//     */
//    @Bean
//    public WebMvcConfigurer corsConfigurer() {
//	return new WebMvcConfigurerAdapter() {
//	    @Override
//	    public void addCorsMappings(CorsRegistry registry) {
//		registry.addMapping("/**");
//	    }
//	};
//    }

}
