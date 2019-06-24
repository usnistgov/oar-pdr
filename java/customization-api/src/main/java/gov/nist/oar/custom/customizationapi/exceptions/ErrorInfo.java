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
package gov.nist.oar.custom.customizationapi.exceptions;



import java.util.Map;
import java.util.Hashtable;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;

/**
 * a simple container for communicating data about a web service error to the web client.  An instance
 * can be automatically converted to a JSON-formatted response by the Spring web framework.
 * <p>
 * Note that, generally, web services should not reflect back inputs from the client back to the client
 * without some scrubbing of that input; this can be a vector for web site injection attacks.
 * <p>
 * This container leverages the Jackson JSON framework (which is used by the Spring Framework) for 
 * serializing this information into JSON.  
 */
@JsonInclude(Include.NON_NULL)
public class ErrorInfo {

    /**
     * the (encoded) URL path.
     */
    public String requestURL = null;

    /**
     * the HTTP method used 
     */
    public String method = null;

    /**
     * the HTTP error status returned
     */
    public int status = 0;

    /**
     * an error message or explanation
     */
    public String message = null;

    /**
     * create the response
     */
    public ErrorInfo(int httpstatus, String reason) {
        status = httpstatus;
        message = reason;
    }

    /**
     * create the response.  GET is assumed as the method used
     */
    public ErrorInfo(String url, int httpstatus, String reason) {
        this(url, httpstatus, reason, "GET");
    }

    /**
     * create the response
     * @param url         the encoded URL accessed by the client.  The output of 
     *                    HttpServletRequest.getRequestURI() is the recommended value as this
     *                    string will generally be encoded.
     * @param httpstatus  the HTTP status code accompanying this error response
     * @param reason      an explanatory error message.  (Note: details are not recommended for 
     *                    status &gt; 500.)
     * @param httpmeth    the HTTP method used by the client (e.g. "GET", "HEAD", etc.)
     */
    public ErrorInfo(String url, int httpstatus, String reason, String httpmeth) {
        status = httpstatus;
        message = reason;
        requestURL = url;
        method = httpmeth;
    }    
}
