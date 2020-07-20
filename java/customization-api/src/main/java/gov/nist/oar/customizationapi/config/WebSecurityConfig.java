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
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Profile;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.builders.WebSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import gov.nist.oar.customizationapi.config.JWTConfig.JWTAuthenticationFilter;
import gov.nist.oar.customizationapi.config.JWTConfig.JWTAuthenticationFilterLocal;
import gov.nist.oar.customizationapi.config.JWTConfig.JWTAuthenticationProvider;
import gov.nist.oar.customizationapi.config.SAMLConfig.SamlSecurityConfig;

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
	private Logger logger = LoggerFactory.getLogger(WebSecurityConfig.class);

	/**
	 * The following configuration should get loaded only in local profile. This is
	 * to test locally without connecting the identity server.
	 * 
	 * @author Deoyani Nandrekar-Heinis
	 *
	 */
	@Configuration
//	@Profile({ "local" }) //This setting can be used to enable the feature based on certain profiles/platforms.
	@ConditionalOnProperty(value = "samlauth.enabled", havingValue = "false", matchIfMissing = false)
	public class SecurityConfig extends WebSecurityConfigurerAdapter {

		@Override
		protected void configure(HttpSecurity security) throws Exception {

			logger.info("#### SAML authentication and authorization service is disabled in this mode. #####");
			security.httpBasic().disable();
			security.formLogin().disable();
			security.cors().and().csrf().disable();
			security.authorizeRequests().antMatchers("/").permitAll();
		}

		/**
		 * Allow following URL patterns without any authentication and authorization
		 */
		@Override
		public void configure(WebSecurity web) throws Exception {
			web.ignoring().antMatchers("/v2/api-docs", "/configuration/ui", "/swagger-resources/**",
					"/configuration/security", "/swagger-ui.html", "/webjars/**", "/pdr/lp/draft/**");
		}
	}

	/**
	 * This bean is created only in local profile this avoids using external SAML id
	 * server.
	 */
	@Configuration
//	@Profile({ "local" }) //This setting can be used to enable the feature based on certain profiles/platforms.
	@ConditionalOnProperty(value = "samlauth.enabled", havingValue = "false", matchIfMissing = false)
	@Order(1)
	public static class RestApiSecurityConfigLocal extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(RestApiSecurityConfigLocal.class);

		@Value("${jwt.secret:testsecret}")
		String secret;

		private static final String apiMatcher = "/pdr/lp/editor/**";

		@Override
		protected void configure(HttpSecurity http) throws Exception {
			logger.info("#### RestApiSecurityConfig HttpSecurity for REST /pdr/lp/editor/ endpoints ###");
			http.addFilterBefore(new JWTAuthenticationFilterLocal(apiMatcher, super.authenticationManager()),
					UsernamePasswordAuthenticationFilter.class);

			http.formLogin().disable();
			http.httpBasic().and().csrf().disable();

		}

		@Override
		protected void configure(AuthenticationManagerBuilder auth) {
			auth.authenticationProvider(new JWTAuthenticationProvider(secret));
		}
	}

	/**
	 * Rest security configuration for rest api
	 */
	@Configuration
	// @Profile({ "prod", "dev", "test", "default" }) //This setting can be used to
	// enable the feature based on certain profiles/platforms.
	@ConditionalOnProperty(value = "samlauth.enabled", havingValue = "true", matchIfMissing = true)
	@Order(1)
	public static class RestApiSecurityConfig extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(RestApiSecurityConfig.class);

		@Value("${jwt.secret:testsecret}")
		String secret;

		private static final String apiMatcher = "/pdr/lp/editor/**";

		@Override
		protected void configure(HttpSecurity http) throws Exception {

			logger.info("#### RestApiSecurityConfig HttpSecurity for REST /pdr/lp/editor/ endpoints ###");
			http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher, super.authenticationManager()),
					UsernamePasswordAuthenticationFilter.class);

			http.authorizeRequests().antMatchers(HttpMethod.PATCH, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.GET, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(HttpMethod.DELETE, apiMatcher).permitAll();
			http.authorizeRequests().antMatchers(apiMatcher).authenticated().and().httpBasic().and().csrf().disable();

		}

		/**
		 * Authentication provider configuration
		 */
		@Override
		protected void configure(AuthenticationManagerBuilder auth) {
			auth.authenticationProvider(new JWTAuthenticationProvider(secret));
		}
	}

	/**
	 * Security configuration for authorization end pointsq
	 */
	@Configuration
	@Order(2)
	public static class AuthSecurityConfig extends WebSecurityConfigurerAdapter {
		private Logger logger = LoggerFactory.getLogger(AuthSecurityConfig.class);

		private static final String apiMatcher = "/auth/**";

//		@Autowired
//		private CustomAccessDeniedHandler accessDeniedHandler;
		@Override
		protected void configure(HttpSecurity http) throws Exception {
			logger.info("Set up authorization related entrypoints.");

			http.exceptionHandling().authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED));
//			http.exceptionHandling().accessDeniedHandler(accessDeniedHandler);
			http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
		}
	}

	/**
	 * Saml security config
	 */
	@Configuration
//	@Profile({ "prod", "dev", "test", "default" }) //This setting can be used to enable the feature based on certain profiles/platforms.
	@ConditionalOnProperty(value = "samlauth.enabled", havingValue = "true", matchIfMissing = true)
	@Import(SamlSecurityConfig.class)
	public static class SamlConfig {

	}

}