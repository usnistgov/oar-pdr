package gov.nist.oar.custom.customizationapi.config.SAMLConfig;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * This filter helps identify the origin of request, allows only the listed URLs
 * to send authentication request. Helps further communication based on token
 * exchage.
 * 
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class CORSFilter implements Filter {

    private String allowedURLs;

    public CORSFilter() {
    }

    public CORSFilter(String listURLs) {
	allowedURLs = listURLs;
    }

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {

    }

//    private final List<String> allowedOrigins = Arrays.asList(alloedURLs); 
    @Override
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain)
	    throws IOException, ServletException {

	List<String> allowedOrigins = Arrays.asList(allowedURLs);
	HttpServletResponse response = (HttpServletResponse) servletResponse;
	HttpServletRequest request = (HttpServletRequest) servletRequest;

//        response.setHeader("Access-Control-Allow-Origin", "http://localhost:4200");
//        response.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,PUT,OPTIONS");
//        response.setHeader("Access-Control-Allow-Headers", "*");
//        response.setHeader("Access-Control-Allow-Credentials", "true");
//        response.setHeader("Access-Control-Max-Age", "180");
	// Access-Control-Allow-Origin

	String origin = request.getHeader("Origin");
	response.setHeader("Access-Control-Allow-Origin", allowedOrigins.contains(origin) ? origin : "");
	response.setHeader("Vary", "Origin");

	// Access-Control-Max-Age
	response.setHeader("Access-Control-Max-Age", "3600");

	// Access-Control-Allow-Credentials
	response.setHeader("Access-Control-Allow-Credentials", "true");

	// Access-Control-Allow-Methods
	response.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE");

	// Access-Control-Allow-Headers
	response.setHeader("Access-Control-Allow-Headers",
		"Origin, X-Requested-With, Content-Type, Accept, withCredentials" + "X-CSRF-TOKEN");

	filterChain.doFilter(request, response);

    }

    @Override
    public void destroy() {

    }
}