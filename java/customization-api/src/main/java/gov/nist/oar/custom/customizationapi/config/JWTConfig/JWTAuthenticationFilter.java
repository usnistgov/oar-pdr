package gov.nist.oar.custom.customizationapi.config.JWTConfig;


import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;
import org.springframework.stereotype.Component;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
//
///**
// * @author 
// */
//public class JWTAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
//
//    public static final String HEADER_SECURITY_TOKEN = "Authorization";
//
//    public JWTAuthenticationFilter(final String matcher, AuthenticationManager authenticationManager) {
//        super(matcher);
//        super.setAuthenticationManager(authenticationManager);
//    }
//
//    @Override
//    public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response) throws IOException, ServletException {
//        final String token = request.getHeader(HEADER_SECURITY_TOKEN);
//        JWTAuthenticationFilter jwtAuthenticationToken = new JWTAuthenticationFilter(token, getAuthenticationManager());
//        return getAuthenticationManager().authenticate((Authentication) jwtAuthenticationToken);
//    }
//
//    @Override
//    protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain, Authentication authResult)
//            throws IOException, ServletException {
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
//}
import java.util.Map;

/**
 * This filter users JWT configuration and filters all the service requests which need authenticated token exchange.
 * @author Deoyani Nandrekar-Heinis
 *
 */
@Component
public class JWTAuthenticationFilter implements Filter {

//private static final Logger logger = LoggerFactory.getLogger(AuthenticationTokenFilter.class);
    public static final String HEADER_SECURITY_TOKEN = "Authorization";
@Override
public void init(FilterConfig fc) throws ServletException {
//    logger.info("Init AuthenticationTokenFilter");
}

@Override
public void doFilter(ServletRequest request, ServletResponse res, FilterChain fc) throws IOException, ServletException {
    SecurityContext context = SecurityContextHolder.getContext();
    final String token = ((HttpServletRequest) request).getHeader(HEADER_SECURITY_TOKEN);
    if(context.getAuthentication().isAuthenticated()) {
	System.out.println("Test:"+token);
    }
//    if (context.getAuthentication() != null && context.getAuthentication().isAuthenticated()) {
//        // do nothing
//    } else {
//        Map<String,String[]> params = req.getParameterMap();
//        if (!params.isEmpty() && params.containsKey("Authorization")) {
//            String token = params.get("Authorization")[0];
//            if (token != null) {
//                //Authentication auth = new TokenAuthentication(token);
//                //SecurityContextHolder.getContext().setAuthentication(auth);
//            }
//        }
//    }

    fc.doFilter(request, res);
}

@Override
public void destroy() {

}


}