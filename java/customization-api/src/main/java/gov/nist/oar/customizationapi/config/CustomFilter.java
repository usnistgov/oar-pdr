package gov.nist.oar.customizationapi.config;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.MediaType;
import org.springframework.web.filter.GenericFilterBean;
import org.springframework.web.filter.OncePerRequestFilter;

//@Order(Ordered.HIGHEST_PRECEDENCE)
//This filter is added to process requests with /saml/login.
public class CustomFilter implements Filter {

	private String allowedURLs;

	public CustomFilter(String listURLs) {
		allowedURLs = listURLs;

	}

	@Override
	public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain chain)
			throws IOException, ServletException {

		boolean isallowed = true;
		HttpServletResponse response = (HttpServletResponse) servletResponse;
		HttpServletRequest request = (HttpServletRequest) servletRequest;

		System.out.println("redirectURL:" + request.getContextPath() + "\n :::" + request.getRequestURI() + " \n :::"
				+ request.getRequestURL());
		try {
			
			String redirectURL = request.getParameterValues("redirectTo")[0];
			if (redirectURL != null) {
				String[] urls = allowedURLs.split(",");
				try {

					for (String urlString : urls) {
						URL url = new URL(redirectURL);
						URL nUrl = new URL(urlString);

						if (redirectURL == null) {
							isallowed = true;

							break;
						}
						if (redirectURL != null && !url.getHost().equalsIgnoreCase(nUrl.getHost())) {

							isallowed = false;

						}
						if (redirectURL != null && url.getHost().equalsIgnoreCase(nUrl.getHost())) {

							isallowed = true;
							break;
						}
					}

				} catch (MalformedURLException e) {

					isallowed = false;
				}
			}


			
		} catch (Exception exp) {

			/**
			 * When there is no redirectURL parameter, it throws an exception here, if the request is coming from any other /saml endpoint other than
			 //saml/login, the filter allows to proceed because the other endpoints are checked by the SAML ext library and any unauthorized 
			  * request is handled and error message is returned accordingly. Ideally this filter should not be called for other endpoints but since
			  * it is getting called, this additional check is added.
			 */
			if(request.getRequestURI().equals("/customization/saml/login ")){
				isallowed = false;
			}
			System.out.println("Exception" + exp.getMessage());
		}

		if (!isallowed) {
			
			response.setStatus(400);
			response.setContentType(MediaType.APPLICATION_JSON_VALUE);
			JSONObject jObject = new JSONObject();
			jObject.put("status", "400");
			jObject.put("requestedURI", request.getRequestURI());
			jObject.put("message", "URL parameter 'redirectTo' does not contain aprroved URL or does not exist .");
			response.getWriter().println(jObject.toString());
			return;

		}
		chain.doFilter(request, response);

	}

}