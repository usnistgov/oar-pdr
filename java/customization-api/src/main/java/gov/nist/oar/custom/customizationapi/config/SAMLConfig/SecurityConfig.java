/**
 * This software was developed at the National Institute of Standards and Technology by employees of
 * the Federal Government in the course of their official duties. Pursuant to title 17 Section 105
 * of the United States Code this software is not subject to copyright protection and is in the
 * public domain. This is an experimental system. NIST assumes no responsibility whatsoever for its
 * use by other parties, and makes no guarantees, expressed or implied, about its quality,
 * reliability, or any other characteristic. We would appreciate acknowledgement if the software is
 * used. This software can be redistributed and/or modified freely provided that any derivative
 * works bear some notice that they are derived from it, and any modified versions bear some notice
 * that they have been modified.
 * @author: Deoyani Nandrekar-Heinis
 */
package gov.nist.oar.custom.customizationapi.config.SAMLConfig;

import javax.inject.Inject;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.context.annotation.Bean;
//import org.springframework.boot.autoconfigure.security.Http401AuthenticationEntryPoint;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.www.BasicAuthenticationFilter;

//import gov.nist.oar.custom.customizationapi.config.JWTConfig.JWTAuthenticationFilter;
import gov.nist.oar.custom.customizationapi.config.JWTConfig.JWTAuthenticationProvider;

/**
 * In this configuration all the end points which need to be secured under
 * authentication service are added. This configuration also sets up token
 * generator and token authorization related configuration and end point
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    /**
     * Rest security configuration for /api/
     */
    @Configuration
    @Order(1)
    public static class RestApiSecurityConfig extends WebSecurityConfigurerAdapter {

	private static final String apiMatcher = "/api/**";
	
//	@Inject
//	JWTAuthenticationFilter authenticationTokenFilter;

 

	@Override
	protected void configure(HttpSecurity http) throws Exception {

//	     http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher,
//	     super.authenticationManager()), BasicAuthenticationFilter.class);
//	    http.addFilterBefore(authenticationTokenFilter, BasicAuthenticationFilter.class);
	    http.authenticationProvider(new JWTAuthenticationProvider());

	    
http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
	}

        @Override
        protected void configure(AuthenticationManagerBuilder auth) {
            auth.authenticationProvider(new JWTAuthenticationProvider());
        }
        
        @Override
        @Bean
        public AuthenticationManager authenticationManagerBean() throws Exception {
            return super.authenticationManagerBean();
        }
    }

    /**
     * Rest security configuration for /api/
     */
    @Configuration
    @Order(2)
    public static class AuthSecurityConfig extends WebSecurityConfigurerAdapter {

	private static final String apiMatcher = "/auth/token";

	@Override
	protected void configure(HttpSecurity http) throws Exception {

	    http.exceptionHandling().authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED));

	    http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
	}
    }

//    @SuppressWarnings("deprecation")
//    @Configuration
//    @Order(3)
//    public class WebMvcConfigurer extends WebMvcConfigurerAdapter {
//	    @Override
//	    public void addCorsMappings(CorsRegistry registry) {
//	        registry.addMapping("/**").allowedOrigins("http://localhost:4200");
//	    }
//	}

    /**
     * Saml security config
     */
    @Configuration
    @Import(SecuritySamlConfig.class)
    public static class SamlConfig {

    }

}