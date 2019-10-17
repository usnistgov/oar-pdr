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

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
//import org.springframework.boot.autoconfigure.security.Http401AuthenticationEntryPoint;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import gov.nist.oar.custom.customizationapi.config.JWTConfig.JWTAuthenticationFilter;
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
	private Logger logger = LoggerFactory.getLogger(RestApiSecurityConfig.class);

//	private static final String apiMatcher = "/api/**";
//
//	@Autowired
//	JWTAuthenticationProvider jwtProvider;
//
//	@Override
//	protected void configure(HttpSecurity http) throws Exception {
//	    logger.info("Configure REST API security endpoints.");
////	    http.addFilterBefore(new JWTAuthenticationFilter(authenticationManager()),
////		    UsernamePasswordAuthenticationFilter.class);
//	    http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher, authenticationManagerBean()), AbstractAuthenticationProcessingFilter.class);
//	    http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
//	}
//
//	@Override
//	@Bean
//	public AuthenticationManager authenticationManagerBean() throws Exception {
//	    return super.authenticationManagerBean();
//	}
//
//	@Override
//	protected void configure(AuthenticationManagerBuilder auth) throws Exception {
//	    auth.authenticationProvider(jwtProvider);
//	    auth.parentAuthenticationManager(authenticationManagerBean());
//	}
	@Value("${jwt.secret:testsecret}")
	String secret;
	
	private static final String apiMatcher = "/api/**";

	@Override
	protected void configure(HttpSecurity http) throws Exception {

	    http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher, super.authenticationManager()),
		    UsernamePasswordAuthenticationFilter.class);

	    http.csrf().disable();
	    http.authorizeRequests().antMatchers(apiMatcher).permitAll().anyRequest()
	    .authenticated();
//	    http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
	}

	@Override
	protected void configure(AuthenticationManagerBuilder auth) {
	    auth.authenticationProvider(new JWTAuthenticationProvider(secret));
	}
    }

    /**
     * Rest security configuration for /api/
     */
    @Configuration
    @Order(2)
    public static class AuthSecurityConfig extends WebSecurityConfigurerAdapter {
	private Logger logger = LoggerFactory.getLogger(AuthSecurityConfig.class);

	private static final String apiMatcher = "/auth/**";

	@Override
	protected void configure(HttpSecurity http) throws Exception {
	    logger.info("AuthSEcurity Config set up http related entrypoints.");

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