package saml.sample.service.serviceprovider;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.PathMatchConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.util.UrlPathHelper;

@SpringBootApplication
public class ServiceproviderApplication {
    

//    /**
//     * configure MVC model, including setting CORS support and semicolon in URLs.
//     * <p>
//     * This gets called as a result of having the @SpringBootApplication annotation.
//     * <p>
//     * The returned configurer allows requested files to have semicolons in them.  By 
//     * default, spring will truncate URLs after the location of a semicolon.  
//     */
//    @SuppressWarnings("deprecation")
//    @Bean
//    public WebMvcConfigurer mvcConfigurer() {
//        return new WebMvcConfigurerAdapter() {
//            @Override
//            public void addCorsMappings(CorsRegistry registry) {
//                registry.addMapping("/**");
//            }
//
//            @Override
//            public void configurePathMatch(PathMatchConfigurer configurer) {
//                UrlPathHelper uhlpr = configurer.getUrlPathHelper();
//                if (uhlpr == null) {
//                    uhlpr = new UrlPathHelper();
//                    configurer.setUrlPathHelper(uhlpr);
//                }
//                uhlpr.setRemoveSemicolonContent(false);
//            }
//        };
//    }
    public static void main(String[] args) {
        SpringApplication.run(ServiceproviderApplication.class);
    }
}