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
package gov.nist.oar.customizationapi.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import gov.nist.oar.customizationapi.config.JWTConfig.JWTAuthenticationFilter;
import gov.nist.oar.customizationapi.config.JWTConfig.JWTAuthenticationProvider;
import gov.nist.oar.customizationapi.config.SAMLConfig.SamlSecurityConfig;
import gov.nist.oar.customizationapi.config.ServiceConfig.ServiceAuthenticationFilter;
import gov.nist.oar.customizationapi.config.ServiceConfig.ServiceAuthenticationProvider;

/**
 * In this configuration all the end points which need to be secured under
 * authentication service are added. This configuration also sets up token
 * generator and token authorization related configuration and end point
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Configuration
@EnableWebSecurity
public class WebSecurityConfig {

	/**
	 * Rest security configuration for rest api
	 */
	@Configuration
	@Order(1)
	public static class RestApiSecurityConfig extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(RestApiSecurityConfig.class);

		@Value("${jwt.secret:testsecret}")
		String secret;

		private static final String apiMatcher = "/pdr/lp/editor/**";

		@Override
		protected void configure(HttpSecurity http) throws Exception {
			logger.info("RestApiSecurityConfig HttpSecurity for REST /api endpoints");
			http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher, super.authenticationManager()),
					UsernamePasswordAuthenticationFilter.class);

			http.authorizeRequests().antMatchers(HttpMethod.PATCH, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.PUT, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.DELETE, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(apiMatcher).authenticated().and().httpBasic().and().csrf().disable();

		}

		@Override
		protected void configure(AuthenticationManagerBuilder auth) {
			auth.authenticationProvider(new JWTAuthenticationProvider(secret));
		}
	}

	/**
	 * Security configuration for authorization end points
	 */
	@Configuration
	@Order(2)
	public static class AuthSecurityConfig extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(AuthSecurityConfig.class);

		private static final String apiMatcher = "/auth/**";

		@Override
		protected void configure(HttpSecurity http) throws Exception {
			logger.info("AuthSecurity Config set up authorization related entrypoints.");

			http.exceptionHandling().authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED));

			http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
		}
	}

	/**
	 * Security configuration for service level authorization end points
	 */
	@Configuration
	@Order(3)
	public static class AuthServiceSecurityConfig extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(AuthServiceSecurityConfig.class);

		private static final String apiMatcher = "/pdr/lp/draft/**";
		@Value("${custom.service.secret:testid}")
		String secret;
		@Override
		protected void configure(HttpSecurity http) throws Exception {
			logger.info("AuthSecurity Config set up http related entrypoints."+secret);
			ServiceAuthenticationFilter serviceFilter = new ServiceAuthenticationFilter(apiMatcher, super.authenticationManager());
			serviceFilter.setSecret(secret);
			http.addFilterBefore(serviceFilter,
					UsernamePasswordAuthenticationFilter.class);
			http.authorizeRequests().antMatchers(HttpMethod.GET, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.PUT, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.DELETE, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(apiMatcher).authenticated().and().httpBasic().and().csrf().disable();

		}

		@Override
		protected void configure(AuthenticationManagerBuilder auth) {
			auth.authenticationProvider(new ServiceAuthenticationProvider());
		}
	}

	 /**
     * Saml security config
     */
    @Configuration
    
    @Import(SamlSecurityConfig.class)
    public static class SamlConfig {

    }
}