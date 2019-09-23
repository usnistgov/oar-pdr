package gov.nist.oar.custom.customizationapi.config.SAMLConfig;

import javax.inject.Inject;

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

import gov.nist.oar.custom.customizationapi.config.JWTConfig.JWTAuthenticationFilter;
import gov.nist.oar.custom.customizationapi.config.JWTConfig.JWTAuthenticationProvider;

/**
 * In this configuration all the endpoints which need to be secured under
 * authentication service are added. This configuration also sets up token
 * generator and token authorization related configuartion and end point
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
	@Inject
	JWTAuthenticationFilter authenticationTokenFilter;

//        @Inject
	JWTAuthenticationProvider authenticationProvider = new JWTAuthenticationProvider();

	@Override
	protected void configure(HttpSecurity http) throws Exception {

	    // http.addFilterBefore(new JWTAuthenticationFilter(apiMatcher,
	    // super.authenticationManager()), UsernamePasswordAuthenticationFilter.class);
	    http.addFilterBefore(authenticationTokenFilter, BasicAuthenticationFilter.class);
	    http.authenticationProvider(authenticationProvider);
	    http.antMatcher(apiMatcher).authorizeRequests().anyRequest().authenticated();
	}

//        @Override
//        protected void configure(AuthenticationManagerBuilder auth) {
//            auth.authenticationProvider(new JWTAuthenticationProvider());
//        }
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