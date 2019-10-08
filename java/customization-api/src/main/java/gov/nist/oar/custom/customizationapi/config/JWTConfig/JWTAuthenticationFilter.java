package gov.nist.oar.custom.customizationapi.config.JWTConfig;

import java.io.IOException;
import java.util.ArrayList;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.InternalAuthenticationServiceException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.www.BasicAuthenticationFilter;

import com.nimbusds.jwt.JWT;

//package gov.nist.oar.custom.customizationapi.config.JWTConfig;
//
//
//import java.io.IOException;
//
//import javax.servlet.FilterChain;
//import javax.servlet.ServletException;
//import javax.servlet.http.HttpServletRequest;
//import javax.servlet.http.HttpServletResponse;
//
//import org.springframework.http.HttpStatus;
//import org.springframework.http.MediaType;
//import org.springframework.security.authentication.AuthenticationManager;
//import org.springframework.security.core.Authentication;
//import org.springframework.security.core.AuthenticationException;
//import org.springframework.security.core.context.SecurityContext;
//import org.springframework.security.core.context.SecurityContextHolder;
//import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;
//import org.springframework.stereotype.Component;
//
///**
// * This filter users JWT configuration and filters all the service requests which need authenticated token exchange.
// * @author Deoyani Nandrekar-Heinis
// *
// */
//
//public class JWTAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
//
////private static final Logger logger = LoggerFactory.getLogger(AuthenticationTokenFilter.class);
//    public static final String HEADER_SECURITY_TOKEN = "Authorization";
//    
//    public JWTAuthenticationFilter(final String matcher, AuthenticationManager authenticationManager) {
//        super(matcher);
//        super.setAuthenticationManager(authenticationManager);
//    }
//
//    @Override
//    public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response) throws IOException, ServletException {
//      final String token = request.getHeader(HEADER_SECURITY_TOKEN).substring(7).trim();
//     
//    JWTAuthenticationToken jwtAuthenticationToken = new JWTAuthenticationToken(token);
//
//    return getAuthenticationManager().authenticate(jwtAuthenticationToken);
//        
//    }
//    
//    @Override
//    protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain, Authentication authResult)
//            throws IOException, ServletException {
//	boolean b = SecurityContextHolder.getContext().getAuthentication().isAuthenticated();
//        SecurityContextHolder.getContext().setAuthentication(authResult);
//        chain.doFilter(request, response);
//    }
//
//    @Override
//    protected void unsuccessfulAuthentication(HttpServletRequest request, HttpServletResponse response, AuthenticationException failed) throws IOException, ServletException {
//        SecurityContextHolder.clearContext();
//        response.setStatus(HttpStatus.UNAUTHORIZED.value());
//        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
//    }
//
////@Override
////public void init(FilterConfig fc) throws ServletException {
//////    logger.info("Init AuthenticationTokenFilter");
////}
//
//
////@Override
////public void doFilter(ServletRequest request, ServletResponse res, FilterChain fc) throws IOException, ServletException {
////    SecurityContext context = SecurityContextHolder.getContext();
////
//////    final String requestTokenHeader = ((HttpServletRequest) request).getHeader(HEADER_SECURITY_TOKEN);
//////    String jwtToken;
//////    System.out.println("context:"+context);
//////    System.out.println("request:"+request);
//////    if (requestTokenHeader != null && requestTokenHeader.startsWith("Bearer ")) {
//////	jwtToken = requestTokenHeader.substring(7);
//////	//String username = jwtTokenUtil.getUsernameFromToken(jwtToken);
//////    }
////    final String token = ((HttpServletRequest) request).getHeader(HEADER_SECURITY_TOKEN);
////    if(context.getAuthentication() != null && context.getAuthentication().isAuthenticated()) {
////	System.out.println("Test:"+token);
////    }
////    try {
////    SignedJWT signedJWT = SignedJWT.parse(token.substring(7));
////
////    }
////    catch(Exception exp) {
////	System.out.println("Exception in parsing token:"+exp.getMessage());
////    }
//////    if (context.getAuthentication() != null && context.getAuthentication().isAuthenticated()) {
//////        // do nothing
//////    } else {
//////        Map<String,String[]> params = request.getParameterMap();
//////        if (!params.isEmpty() && params.containsKey("Authorization")) {
//////            String token = params.get("Authorization")[0];
//////            if (token != null) {
////////                Authentication auth = new TokenAuthentication(token);
////////                SecurityContextHolder.getContext().setAuthentication(auth);
//////            }
//////        }
//////    }
////
////    fc.doFilter(request, res);
////}
//
//
////@Override
////public void destroy() {
////
////}
//
//
////public JWTAuthenticationFilter(String matcher, AuthenticationManager authenticationManager) {
////  super(matcher);
////  super.setAuthenticationManager(authenticationManager);
////}    
////
////@Override
////public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response) throws IOException, ServletException {
////    final String token = request.getHeader(HEADER_SECURITY_TOKEN);
////    JWTAuthenticationToken jwtAuthenticationToken = new JWTAuthenticationToken(token);
////    return getAuthenticationManager().authenticate(jwtAuthenticationToken);
////}
////
////@Override
////protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain, Authentication authResult)
////        throws IOException, ServletException {
////    SecurityContextHolder.getContext().setAuthentication(authResult);
////    chain.doFilter(request, response);
////}
////
////@Override
////protected void unsuccessfulAuthentication(HttpServletRequest request, HttpServletResponse response, AuthenticationException failed) throws IOException, ServletException {
////    SecurityContextHolder.clearContext();
////    response.setStatus(HttpStatus.UNAUTHORIZED.value());
////    response.setContentType(MediaType.APPLICATION_JSON_VALUE);
////}
//
//
//
////public JWTAuthenticationFilter() {
////    super("/api/**");
////}
////
////@Override
////protected boolean requiresAuthentication(HttpServletRequest request, HttpServletResponse response) {
////    return true;
////}
////
////@Override
////public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response) throws AuthenticationException {
////
////    String header = request.getHeader("Authorization");
////
////    if (header == null || !header.startsWith("Bearer ")) {
////        try {
////	    throw new Exception("No JWT token found in request headers");
////	} catch (Exception e) {
////	    // TODO Auto-generated catch block
////	    e.printStackTrace();
////	}
////    }
////
////    String authToken = header.substring(7);
////
////    JWTAuthenticationToken authRequest = new JWTAuthenticationToken(authToken);
////
////    return getAuthenticationManager().authenticate(authRequest);
////}
////
////@Override
////protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain, Authentication authResult)
////        throws IOException, ServletException {
////    super.successfulAuthentication(request, response, chain, authResult);
////
////    // As this authentication is in HTTP header, after success we need to continue the request normally
////    // and return the response as if the resource was not secured at all
////    chain.doFilter(request, response);
////}
////@Override
////@Autowired
////public void setAuthenticationManager(AuthenticationManager authenticationManager) {
////    super.setAuthenticationManager(authenticationManager);
////}
//
//}
//This should be renamed as authorization filter
//JWTAuthorizationFilter
public class JWTAuthenticationFilter extends BasicAuthenticationFilter {

    private static final Logger logger =LoggerFactory.getLogger(JWTAuthenticationFilter.class);
    public static final String HEADER_SECURITY_TOKEN = "Authorization";

//  @Autowired
//  private JWTAuthenticationProvider authenticationManager;

    public JWTAuthenticationFilter(AuthenticationManager authManager) {

	super(authManager);

    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
	    throws IOException, ServletException {
	logger.info("Security token header invoked.");
	String header = req.getHeader(HEADER_SECURITY_TOKEN);

	if (header == null || !header.startsWith("Bearer")) {
	    //chain.doFilter(req, res);
	    SecurityContextHolder.clearContext();
	    res.setStatus(HttpStatus.UNAUTHORIZED.value());
	    res.setContentType(MediaType.APPLICATION_JSON_VALUE);
	    res.getWriter().write("{\"message\": \"No user token found or is not of proper type.\" }");
	    return;
	}
	try {
	JWTAuthenticationProvider authenticationManager = new JWTAuthenticationProvider();
	authenticationManager.authenticate(new JWTAuthenticationToken(header.substring(7)));

//        UsernamePasswordAuthenticationToken authentication = getAuthentication(req);
        SecurityContextHolder.getContext().setAuthentication(new JWTAuthenticationToken(header.substring(7)));
	chain.doFilter(req, res);
	}catch(InternalAuthenticationServiceException exp) {
	    logger.error("There is an error authorizing token requested.");
	    res.setStatus(HttpStatus.UNAUTHORIZED.value());
	    res.setContentType(MediaType.APPLICATION_JSON_VALUE);
	    res.getWriter().write("{\"message\":\"User token is not authorized.\"");
	   
	}

    }

//    private UsernamePasswordAuthenticationToken getAuthentication(HttpServletRequest request) {
//        String token = request.getHeader(HEADER_SECURITY_TOKEN);
//        if (token != null) {
//            // parse the token.
//            String user =" testuser";
//
//            if (user != null) {
//                return new UsernamePasswordAuthenticationToken(user, null, new ArrayList<>());
//            }
//            return null;
//        }
//        return null;
//    }
}