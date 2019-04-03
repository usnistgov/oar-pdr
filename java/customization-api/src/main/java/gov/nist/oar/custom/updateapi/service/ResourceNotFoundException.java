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
package gov.nist.oar.custom.updateapi.service;

/**
 * @author Deoyani Nandrekar-Heinis
 *
 */
public class ResourceNotFoundException extends RuntimeException {
    private String requestUrl = "";

    /**
     * ResourceNotFoundException for given Id
     * 
     * @param id
     */
    public ResourceNotFoundException(int id) {
	super("ResourceNotFoundException with id=" + id);
    }

    /**
     * ResourceNotFoundException
     */
    public ResourceNotFoundException() {
	super("Resource you are looking for is not available.");
    }

    /***
     * ResourceNotFoundException for requestUrl
     * 
     * @param requestUrl
     *            String
     */
    public ResourceNotFoundException(String requestUrl) {

	super("Resource you are looking for is not available.");
	this.setRequestUrl(requestUrl);
    }

    /***
     * GetRequestURL
     * 
     * @return String
     */
    public String getRequestUrl() {
	return this.requestUrl;
    }

    /***
     * Set Request URL
     * 
     * @param url
     *            String
     */
    public void setRequestUrl(String url) {
	this.requestUrl = url;
    }
}
