package gov.nist.oar.customizationapi.web;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Component
public class CustomAccessDeniedHandler implements AccessDeniedHandler {
 
    @Override
    public void handle
      (HttpServletRequest request, HttpServletResponse response, AccessDeniedException ex) 
      throws IOException, ServletException {
    	throw new IOException("TEST");
        //response.sendRedirect("/my-error-page");
    }
}