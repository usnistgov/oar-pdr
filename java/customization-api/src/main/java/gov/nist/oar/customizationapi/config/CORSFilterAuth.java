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
public class CORSFilterAuth implements Filter {

	private String allowedURLs;

	public CORSFilterAuth() {
	}

	public CORSFilterAuth(String listURLs) {
		allowedURLs = listURLs;
	}

	@Override
	public void init(FilterConfig filterConfig) throws ServletException {

	}

	@Override
	public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain)
			throws IOException, ServletException {

		List<String> allowedOrigins = Arrays.asList(allowedURLs);
		HttpServletResponse response = (HttpServletResponse) servletResponse;
		HttpServletRequest request = (HttpServletRequest) servletRequest;

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

		
		if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            response.setStatus(HttpServletResponse.SC_OK);
        } else {
        	filterChain.doFilter(request, response);
        }
		filterChain.doFilter(request, response);

	}

	@Override
	public void destroy() {

	}
}