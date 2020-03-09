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
package gov.nist.oar.customizationapi.config.SAMLConfig;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Timer;

import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.MultiThreadedHttpConnectionManager;
import org.apache.commons.httpclient.protocol.Protocol;
import org.apache.commons.httpclient.protocol.ProtocolSocketFactory;
import org.apache.velocity.app.VelocityEngine;
import org.opensaml.saml2.metadata.provider.MetadataProvider;
import org.opensaml.saml2.metadata.provider.MetadataProviderException;
import org.opensaml.saml2.metadata.provider.ResourceBackedMetadataProvider;
import org.opensaml.util.resource.ResourceException;
import org.opensaml.xml.parse.StaticBasicParserPool;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.config.MethodInvokingFactoryBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.builders.WebSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.saml.SAMLAuthenticationProvider;
import org.springframework.security.saml.SAMLBootstrap;
import org.springframework.security.saml.SAMLEntryPoint;
import org.springframework.security.saml.SAMLLogoutFilter;
import org.springframework.security.saml.SAMLLogoutProcessingFilter;
import org.springframework.security.saml.SAMLProcessingFilter;
import org.springframework.security.saml.SAMLRelayStateSuccessHandler;
import org.springframework.security.saml.context.SAMLContextProviderImpl;
import org.springframework.security.saml.context.SAMLContextProviderLB;
import org.springframework.security.saml.key.JKSKeyManager;
import org.springframework.security.saml.key.KeyManager;
import org.springframework.security.saml.log.SAMLDefaultLogger;
import org.springframework.security.saml.metadata.CachingMetadataManager;
import org.springframework.security.saml.metadata.ExtendedMetadata;
import org.springframework.security.saml.metadata.ExtendedMetadataDelegate;
import org.springframework.security.saml.metadata.MetadataDisplayFilter;
import org.springframework.security.saml.metadata.MetadataGenerator;
import org.springframework.security.saml.metadata.MetadataGeneratorFilter;
import org.springframework.security.saml.parser.ParserPoolHolder;
import org.springframework.security.saml.processor.HTTPPostBinding;
import org.springframework.security.saml.processor.HTTPRedirectDeflateBinding;
import org.springframework.security.saml.processor.SAMLBinding;
import org.springframework.security.saml.processor.SAMLProcessorImpl;
import org.springframework.security.saml.trust.httpclient.TLSProtocolConfigurer;
import org.springframework.security.saml.trust.httpclient.TLSProtocolSocketFactory;
import org.springframework.security.saml.userdetails.SAMLUserDetailsService;
import org.springframework.security.saml.util.VelocityFactory;
import org.springframework.security.saml.websso.SingleLogoutProfile;
import org.springframework.security.saml.websso.SingleLogoutProfileImpl;
import org.springframework.security.saml.websso.WebSSOProfile;
import org.springframework.security.saml.websso.WebSSOProfileConsumer;
import org.springframework.security.saml.websso.WebSSOProfileConsumerHoKImpl;
import org.springframework.security.saml.websso.WebSSOProfileConsumerImpl;
import org.springframework.security.saml.websso.WebSSOProfileImpl;
import org.springframework.security.saml.websso.WebSSOProfileOptions;
import org.springframework.security.web.DefaultSecurityFilterChain;
import org.springframework.security.web.FilterChainProxy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.channel.ChannelProcessingFilter;
import org.springframework.security.web.authentication.SavedRequestAwareAuthenticationSuccessHandler;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;
import org.springframework.security.web.authentication.logout.HttpStatusReturningLogoutSuccessHandler;
import org.springframework.security.web.authentication.logout.LogoutHandler;
import org.springframework.security.web.authentication.logout.SecurityContextLogoutHandler;
import org.springframework.security.web.authentication.www.BasicAuthenticationFilter;
import org.springframework.security.web.session.SessionManagementFilter;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;

import gov.nist.oar.customizationapi.exceptions.ConfigurationException;
import gov.nist.oar.customizationapi.service.SamlUserDetailsService;

/**
 * This class reads configurations values from config server and set ups the
 * SAML service related parameters. It also helps to initialize different SAML
 * endpoints, creates handshake with SAML identity service It sets up saml relay
 * point to create further communication between user application with the
 * server.
 * 
 * @author Deoyani Nandrekar-Heinis
 */
@Configuration
//@EnableWebSecurity
public class SamlSecurityConfig extends WebSecurityConfigurerAdapter {
	private static Logger logger = LoggerFactory.getLogger(SamlSecurityConfig.class);

	/**
	 * Entityid for the SAML service provider, in this case customization service
	 */
	@Value("${saml.metdata.entityid:testid}")
	String entityId;

	/**
	 * EntityURL for the service provider, in this case customization base url
	 */
	@Value("${saml.metadata.entitybaseUrl:testurl}")
	String entityBaseURL;

	/**
	 * Keystore location
	 */
	@Value("${saml.keystore.path:testpath}")
	String keyPath;

	/**
	 * Keystore store pass
	 */
	@Value("${saml.keystroe.storepass:testpass}")
	String keystorePass;

	/**
	 * Keystrore key
	 */
	@Value("${saml.keystore.key:testkey}")
	String keyAlias;

	/**
	 * Keystore key pass
	 */
	@Value("${saml.keystore.keypass:keypass}")
	String keyPass;

	/**
	 * Federation URL or File
	 */
	@Value("${auth.federation.metadata:fedmetadata}")
	String federationMetadata;

	/**
	 * SAML scheme user
	 */
	@Value("${saml.scheme:samlscheme}")
	String samlScheme;

	/**
	 * SAML server name
	 */
	@Value("${saml.server.name:server}")
	String samlServer;

	/**
	 * SAML context path
	 */
	@Value("${saml.server.context-path:context}")
	String samlContext;

	/**
	 * SAML application URL
	 */
	@Value("${application.url:http://localhost:4200}")
	String applicationURL;

	/**
	 * Default single sign on profile options are set up here, we can add relaystate
	 * for redirect here as well.
	 * 
	 * @return
	 * @throws ConfigurationException
	 */
	@Bean
	public WebSSOProfileOptions defaultWebSSOProfileOptions() throws ConfigurationException {
		logger.info("Setting up authticated service redirect by setting web sso profiles.");
		WebSSOProfileOptions webSSOProfileOptions = new WebSSOProfileOptions();
		webSSOProfileOptions.setIncludeScoping(false);
		/// Adding this force authenticate on failure to validate SAML cache
		webSSOProfileOptions.setForceAuthN(true);
		// Relay state can also be set here it will always go to this URL once
		// authenticated
		// webSSOProfileOptions.setRelayState("https://data.nist.gov/sdp");
		return webSSOProfileOptions;
	}

	/**
	 * When SAML protected resource is called this entry point is used to connect to
	 * SAML service provider and get the authentication
	 * 
	 * @return
	 * @throws ConfigurationException
	 */
	@Bean
	public SAMLEntryPoint samlEntryPoint() throws ConfigurationException {
		logger.info("SAML Entry point. with application url " + applicationURL);
		SAMLEntryPoint samlEntryPoint = new SamlWithRelayStateEntryPoint(applicationURL);
		samlEntryPoint.setDefaultProfileOptions(defaultWebSSOProfileOptions());
		return samlEntryPoint;
	}

	/**
	 * Metadatadisplay filter is called to use IDP metadata and set up SP service
	 * 
	 * @return
	 */
	@Bean
	public MetadataDisplayFilter metadataDisplayFilter() {
		return new MetadataDisplayFilter();
	}

	/**
	 * Authentication failure handler
	 * 
	 * @return
	 */
	@Bean
	public SimpleUrlAuthenticationFailureHandler authenticationFailureHandler() {
		logger.info("SAML authentication failure!!");
		return new SimpleUrlAuthenticationFailureHandler();
	}

	/**
	 * Authentication success handler
	 * 
	 * @return
	 */
	@Bean
	public SavedRequestAwareAuthenticationSuccessHandler successRedirectHandler() {
		SavedRequestAwareAuthenticationSuccessHandler successRedirectHandler = new SAMLRelayStateSuccessHandler();
		return successRedirectHandler;
	}

	/**
	 * SAML Web SSO processing filter
	 * 
	 * @return SAMLProcessingFilter
	 * @throws ConfigurationException
	 */
	@Bean
	public SAMLProcessingFilter samlWebSSOProcessingFilter() throws ConfigurationException {
		logger.info("SAMLProcessingFilter adding authentication manager.");
		SAMLProcessingFilter samlWebSSOProcessingFilter = new SAMLProcessingFilter();
		try {
			samlWebSSOProcessingFilter.setAuthenticationManager(authenticationManager());
		} catch (Exception e) {
			throw new ConfigurationException("Exception while setting up Authentication Manager:" + e.getMessage());
		}
		samlWebSSOProcessingFilter.setAuthenticationSuccessHandler(successRedirectHandler());
		samlWebSSOProcessingFilter.setAuthenticationFailureHandler(authenticationFailureHandler());
		return samlWebSSOProcessingFilter;
	}

	/**
	 * successLogoutHandler
	 * 
	 * @return HttpStatusReturningLogoutSuccessHandler
	 */
	@Bean
	public HttpStatusReturningLogoutSuccessHandler successLogoutHandler() {
		return new HttpStatusReturningLogoutSuccessHandler();
	}

	/**
	 * SecurityContextLogoutHandler handler
	 * 
	 * @return SecurityContextLogoutHandler
	 */
	@Bean
	public SecurityContextLogoutHandler logoutHandler() {
		logger.info("In SecurityContextLogoutHandler, setinvalid httpsession and clear authentication to true.");
		SecurityContextLogoutHandler logoutHandler = new SecurityContextLogoutHandler();
		logoutHandler.setInvalidateHttpSession(true);
		logoutHandler.setClearAuthentication(true);
		return logoutHandler;
	}

	/**
	 * SAML logout filter
	 * 
	 * @return SAMLLogoutFilter
	 */
	@Bean
	public SAMLLogoutFilter samlLogoutFilter() {
		return new SAMLLogoutFilter(successLogoutHandler(), new LogoutHandler[] { logoutHandler() },
				new LogoutHandler[] { logoutHandler() });
	}

	/**
	 * SAML logout processing filter
	 * 
	 * @return
	 */
	@Bean
	public SAMLLogoutProcessingFilter samlLogoutProcessingFilter() {
		return new SAMLLogoutProcessingFilter(successLogoutHandler(), logoutHandler());
	}

	/**
	 * Metadatagenerator
	 * 
	 * @return MetadataGenerator
	 * @throws ConfigurationException
	 */
	@Bean
	public MetadataGeneratorFilter metadataGeneratorFilter() throws ConfigurationException {
		return new MetadataGeneratorFilter(metadataGenerator());
	}

	/**
	 * Generates metadata for the service provider
	 * 
	 * @return MetadataGenerator
	 * @throws ConfigurationException
	 */
	@Bean
	public MetadataGenerator metadataGenerator() throws ConfigurationException {
		logger.info("Metadata generator : sets the entity id and base url to establish communication with ID server.");
		MetadataGenerator metadataGenerator = new MetadataGenerator();
		metadataGenerator.setEntityId(entityId);
		metadataGenerator.setEntityBaseURL(entityBaseURL);
		metadataGenerator.setExtendedMetadata(extendedMetadata());
		metadataGenerator.setIncludeDiscoveryExtension(false);
		metadataGenerator.setKeyManager(keyManager());
		return metadataGenerator;
	}

	/**
	 * To load the keystore key with keypass
	 * 
	 * @return KeyManager
	 * @throws ConfigurationException
	 */
	@Bean
	public KeyManager keyManager() throws ConfigurationException {
		logger.info("Read keystore key.");
		try {
			// ClassPathResource storeFile = new ClassPathResource(keyPath);
			Resource storeFile = new FileSystemResource(keyPath);
			String storePass = keystorePass;
			Map<String, String> passwords = new HashMap<>();
			passwords.put(keyAlias, keyPass);
			return new JKSKeyManager(storeFile, storePass, passwords, keyAlias);
		} catch (Exception e) {
			throw new ConfigurationException("Exception while loding keystore key, " + e.getMessage());
		}
	}

	/***
	 * Extended Metadata
	 * 
	 * @return ExtendedMetadata
	 */
	@Bean
	public ExtendedMetadata extendedMetadata() {
		ExtendedMetadata extendedMetadata = new ExtendedMetadata();
		extendedMetadata.setIdpDiscoveryEnabled(false);
		extendedMetadata.setSignMetadata(false);
		return extendedMetadata;
	}

	/**
	 * Set up filter chain for the SAML authentication system, to connect to IDP
	 * 
	 * @return FilterChainProxy
	 * @throws ConfigurationException
	 */
	@Bean
	public FilterChainProxy samlChainFilter() throws ConfigurationException {
		logger.info("Setting up different saml filters and endpoints");
		List<SecurityFilterChain> chains = new ArrayList<>();

		chains.add(new DefaultSecurityFilterChain(new AntPathRequestMatcher("/saml/metadata/**"),
				metadataDisplayFilter()));

		chains.add(new DefaultSecurityFilterChain(new AntPathRequestMatcher("/saml/login/**"), samlEntryPoint()));

		chains.add(new DefaultSecurityFilterChain(new AntPathRequestMatcher("/saml/sso/**"),
				samlWebSSOProcessingFilter()));

		chains.add(new DefaultSecurityFilterChain(new AntPathRequestMatcher("/saml/logout/**"), samlLogoutFilter()));

		chains.add(new DefaultSecurityFilterChain(new AntPathRequestMatcher("/saml/singleLogout/**"),
				samlLogoutProcessingFilter()));

		return new FilterChainProxy(chains);
	}

	/**
	 * Making sure TLS security
	 * 
	 * @return TLSProtocolConfigurer
	 */
	@Bean
	public TLSProtocolConfigurer tlsProtocolConfigurer() {
		return new TLSProtocolConfigurer();
	}

	/**
	 * 
	 * @return ProtocolSocketFactory
	 * @throws ConfigurationException
	 */
	@Bean
	public ProtocolSocketFactory socketFactory() throws ConfigurationException {
		return new TLSProtocolSocketFactory(keyManager(), null, "default");
	}

	/**
	 * 
	 * @return Protocol
	 * @throws ConfigurationException
	 */
	@Bean
	public Protocol socketFactoryProtocol() throws ConfigurationException {
		return new Protocol("https", socketFactory(), 443);
	}

	/**
	 * 
	 * @return MethodInvokingFactoryBean
	 * @throws ConfigurationException
	 */
	@Bean
	public MethodInvokingFactoryBean socketFactoryInitialization() throws ConfigurationException {
		logger.info("Socket factory initialization.");
		MethodInvokingFactoryBean methodInvokingFactoryBean = new MethodInvokingFactoryBean();
		methodInvokingFactoryBean.setTargetClass(Protocol.class);
		methodInvokingFactoryBean.setTargetMethod("registerProtocol");
		Object[] args = { "https", socketFactoryProtocol() };
		methodInvokingFactoryBean.setArguments(args);
		return methodInvokingFactoryBean;
	}

	/**
	 * XML parsing configuration
	 * 
	 * @return VelocityEngine
	 */
	@Bean
	public VelocityEngine velocityEngine() {
		return VelocityFactory.getEngine();
	}

	/**
	 * XML parsing configuration
	 * 
	 * @return StaticBasicParserPool
	 */
	@Bean(initMethod = "initialize")
	public StaticBasicParserPool parserPool() {
		return new StaticBasicParserPool();
	}

	/**
	 * XML parsing configuration
	 * 
	 * @return ParserPoolHolder
	 */
	@Bean(name = "parserPoolHolder")
	public ParserPoolHolder parserPoolHolder() {
		return new ParserPoolHolder();
	}

	/**
	 * SAML Binding which depends on IDP specifications
	 * 
	 * @return HTTPPostBinding
	 */
	@Bean
	public HTTPPostBinding httpPostBinding() {
		return new HTTPPostBinding(parserPool(), velocityEngine());
	}

	/**
	 * SAML Binding which depends on IDP specifications
	 * 
	 * @return HTTPRedirectDeflateBinding
	 */
	@Bean
	public HTTPRedirectDeflateBinding httpRedirectDeflateBinding() {
		return new HTTPRedirectDeflateBinding(parserPool());
	}

	/**
	 * SAML Binding which depends on IDP specifications
	 * 
	 * @return SAMLProcessorImpl
	 */
	@Bean
	public SAMLProcessorImpl processor() {
		Collection<SAMLBinding> bindings = new ArrayList<>();
		bindings.add(httpRedirectDeflateBinding());
		bindings.add(httpPostBinding());
		return new SAMLProcessorImpl(bindings);
	}

	/**
	 * Return httpclient to handle multithread
	 * 
	 * @return HttpClient
	 */
	@Bean
	public HttpClient httpClient() {
		return new HttpClient(multiThreadedHttpConnectionManager());
	}

	/**
	 * Multiple thread
	 * 
	 * @return MultiThreadedHttpConnectionManager
	 */
	@Bean
	public MultiThreadedHttpConnectionManager multiThreadedHttpConnectionManager() {
		return new MultiThreadedHttpConnectionManager();
	}

	/**
	 * To initialize SAML library with spring boot initialization
	 * 
	 * @return SAMLBootstrap
	 */
	@Bean
	public static SAMLBootstrap sAMLBootstrap() {
		return new SAMLBootstrap();
	}

	/**
	 * Default logger to make sure all SAML requests get logged into
	 * 
	 * @return SAMLDefaultLogger
	 */
	@Bean
	public SAMLDefaultLogger samlLogger() {
		return new SAMLDefaultLogger();
	}

	/**
	 * Parsing request/responses to make sure which SAML IDP or SP deal with it
	 * 
	 * @return SAMLContextProviderImpl
	 * @throws ConfigurationException
	 */
	@Bean
	public SAMLContextProviderImpl contextProvider() throws ConfigurationException {
		logger.info("SAML context provider.");
		SAMLContextProviderLB samlContextProviderLB = new SAMLContextProviderLB();
		samlContextProviderLB.setScheme(samlScheme);
		samlContextProviderLB.setServerName(samlServer);
		samlContextProviderLB.setServerPort(443);
		samlContextProviderLB.setIncludeServerPortInRequestURL(true);
		samlContextProviderLB.setContextPath(samlContext);
		samlContextProviderLB.setStorageFactory(new org.springframework.security.saml.storage.EmptyStorageFactory());
		return samlContextProviderLB;
	}

	/***
	 * SAML 2.0 WebSSO Assertion Consumer
	 * 
	 * @return WebSSOProfileConsumer
	 */
	@Bean
	public WebSSOProfileConsumer webSSOprofileConsumer() {
		return new WebSSOProfileConsumerImpl();
	}

	/**
	 * SAML 2.0 Web SSO profile
	 * 
	 * @return WebSSOProfile
	 */
	@Bean
	public WebSSOProfile webSSOprofile() {
		return new WebSSOProfileImpl();
	}

	/***
	 * SAML 2.0 Holder-of-Key WebSSO Assertion Consumer
	 * 
	 * @return WebSSOProfileConsumerHoKImpl
	 */
	@Bean
	public WebSSOProfileConsumerHoKImpl hokWebSSOprofileConsumer() {
		return new WebSSOProfileConsumerHoKImpl();
	}

	/**
	 * SAML 2.0 Holder-of-Key Web SSO profile
	 * 
	 * @return WebSSOProfileConsumerHoKImpl
	 */
	@Bean
	public WebSSOProfileConsumerHoKImpl hokWebSSOProfile() {
		return new WebSSOProfileConsumerHoKImpl();
	}

	/**
	 * Logout profile setting.
	 * 
	 * @return SingleLogoutProfile
	 */
	@Bean
	public SingleLogoutProfile logoutprofile() {
		return new SingleLogoutProfileImpl();
	}

	/**
	 * Read the federation metadata and load to extended metadata
	 * 
	 * @return ExtendedMetadataDelegate
	 * @throws ConfigurationException
	 */
	@Bean
	public ExtendedMetadataDelegate idpMetadata() throws ConfigurationException {
		logger.info("Read the federation metadata provided by identity provider.");

		try {
			Timer backgroundTaskTimer = new Timer(true);

			org.opensaml.util.resource.FilesystemResource fpath = new org.opensaml.util.resource.FilesystemResource(
					federationMetadata);
			ResourceBackedMetadataProvider resourceBackedMetadataProvider = new ResourceBackedMetadataProvider(
					backgroundTaskTimer, fpath);

			/**
			 * This code is used if the metadata url is available and can be used directly.
			 */
			// new ClasspathResource(federationMetadata));
//        String fedMetadataURL = "https://sts.nist.gov/federationmetadata/2007-06/federationmetadata.xml";
//	HTTPMetadataProvider httpMetadataProvider = new HTTPMetadataProvider(
//			backgroundTaskTimer, httpClient(), fedMetadataURL);
//	httpMetadataProvider.setParserPool(parserPool());
//	        ExtendedMetadataDelegate extendedMetadataDelegate =
//          new ExtendedMetadataDelegate(httpMetadataProvider , extendedMetadata());
			resourceBackedMetadataProvider.setParserPool(parserPool());

			ExtendedMetadataDelegate extendedMetadataDelegate = new ExtendedMetadataDelegate(
					resourceBackedMetadataProvider, extendedMetadata());

			//// **** just set this to false to solve the issue signature trust specific to
			//// current IDP
			extendedMetadataDelegate.setMetadataTrustCheck(false);
			extendedMetadataDelegate.setMetadataRequireSignature(false);
			return extendedMetadataDelegate;
		} catch (MetadataProviderException mpEx) {
			throw new ConfigurationException(
					"MetadataProviderException while reading federation metadata." + mpEx.getMessage());
		} catch (ResourceException rEx) {
			throw new ConfigurationException(
					"ResourceException while reading federationmetadata for SAML identifier, " + rEx.getMessage());
		}
	}

	/**
	 * 
	 * @return CachingMetadataManager
	 * @throws ConfigurationException
	 * @throws MetadataProviderException
	 */
	@Bean
	@Qualifier("metadata")
	public CachingMetadataManager metadata() throws ConfigurationException, MetadataProviderException {
		List<MetadataProvider> providers = new ArrayList<>();
		providers.add(idpMetadata());
		return new CachingMetadataManager(providers);
	}

	/**
	 * 
	 * @return SAMLUserDetailsService
	 */
	@Bean
	public SAMLUserDetailsService samlUserDetailsService() {
		return new SamlUserDetailsService();
	}

	/**
	 * Returns Authentication provider which is capable of verifying validity of a
	 * SAMLAuthenticationToken
	 * 
	 * @return SAMLAuthenticationProvider
	 */
	@Bean
	public SAMLAuthenticationProvider samlAuthenticationProvider() {
		SAMLAuthenticationProvider samlAuthenticationProvider = new SAMLAuthenticationProvider();
		samlAuthenticationProvider.setUserDetails(samlUserDetailsService());
		samlAuthenticationProvider.setForcePrincipalAsString(false);
		return samlAuthenticationProvider;
	}

	/**
	 * Configure authentication manager.
	 */
	@Override
	protected void configure(AuthenticationManagerBuilder auth) {
		auth.authenticationProvider(samlAuthenticationProvider());
	}

	/**
	 * Set up filter for cross origin requests, here it is read from configserver
	 * and applicationURL is angular application URL
	 * 
	 * @return CORSFilter
	 */
	@Bean
	CORSFilter corsFilter() {
		logger.info("CORS filter setting for application:" + applicationURL);
		CORSFilter filter = new CORSFilter(applicationURL);
		return filter;
	}

	/**
	 * Allow following URL patterns without any authentication and authorization
	 */
	@Override
	public void configure(WebSecurity web) throws Exception {
		web.ignoring().antMatchers("/v2/api-docs", "/configuration/ui", "/swagger-resources/**",
				"/configuration/security", "/swagger-ui.html", "/webjars/**","/pdr/lp/draft/**");
	}

	/**
	 * Test These are all http security configurations for different endpoints.
	 */
	@Override
	protected void configure(HttpSecurity http) throws ConfigurationException {
		logger.info("Set up http security related filters for saml entrypoints");

		try {
			http.addFilterBefore(corsFilter(), SessionManagementFilter.class).exceptionHandling()
					.authenticationEntryPoint(samlEntryPoint());

			http.csrf().disable();

			http.addFilterBefore(metadataGeneratorFilter(), ChannelProcessingFilter.class).addFilterAfter(samlChainFilter(),
					BasicAuthenticationFilter.class);

			http.authorizeRequests().antMatchers("/error").permitAll().antMatchers("/saml/**").permitAll().anyRequest()
					.authenticated();

			http.logout().logoutSuccessUrl("/");

		} catch (Exception e) {
			throw new ConfigurationException("Exception in SAML security config for HttpSecurity," + e.getMessage());
		}

	}

//  private Timer backgroundTaskTimer;
//	private MultiThreadedHttpConnectionManager multiThreadedHttpConnectionManager;
//
//	public void init() {
//		this.backgroundTaskTimer = new Timer(true);
//		this.multiThreadedHttpConnectionManager = new MultiThreadedHttpConnectionManager();
//	}
//
//	public void shutdown() {
//		this.backgroundTaskTimer.purge();
//		this.backgroundTaskTimer.cancel();
//		this.multiThreadedHttpConnectionManager.shutdown();
//	}
}