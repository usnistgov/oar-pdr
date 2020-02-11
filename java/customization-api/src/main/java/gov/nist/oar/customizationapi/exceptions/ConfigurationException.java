package gov.nist.oar.customizationapi.exceptions;

/**
 * an exception indicating an error while assembling and configuring an
 * application. When this exception is caught by the
 * <a href="https://spring.io/" target="_top">spring boot framework</a>,
 * execution ceases.
 */
public class ConfigurationException extends Exception {

	/**
	 * 
	 */
	private static final long serialVersionUID = -3478456363037007927L;
	protected String parameter = null;
	protected String reason = null;

	/**
	 * Create an exception with an arbitrary message
	 */
	public ConfigurationException(String msg) {
		super(msg);
	}

	/**
	 * Create an exception about a specific parameter. The parameter will be
	 * combined with the given reason.
	 * 
	 * @param param  the configuration parameter name whose value (or lack thereof)
	 *               has resulted in an error.
	 * @param reason an explanation of what is wrong with the parameter. This will
	 *               be combined with the parameter name to created the exception
	 *               message (returned via {@code getMessage()}.
	 * @param cause  An underlying exception that was thrown as a result of the
	 *               parameter value.
	 */
	public ConfigurationException(String param, String reason) {
		this(param, reason, null);
	}

	/**
	 * Create an exception about a specific parameter. The parameter will be
	 * combined with the given reason.
	 * 
	 * @param param  the configuration parameter name whose value (or lack thereof)
	 *               has resulted in an error.
	 * @param reason an explanation of what is wrong with the parameter. This will
	 *               be combined with the parameter name to created the exception
	 *               message (returned via {@code getMessage()}.
	 * @param cause  An underlying exception that was thrown as a result of the
	 *               parameter value.
	 */
	public ConfigurationException(String param, String reason, Throwable cause) {
		super(param + ": " + reason, cause);
		parameter = param;
		this.reason = reason;
	}

	/**
	 * return the name of the parameter that was incorrectly set
	 */
	public String getParameterName() {
		return parameter;
	}

	/**
	 * return the explanation of how parameter is incorrect. This will not include
	 * the parameter name.
	 * 
	 * {@see #getParamterName} {@see #getMessage}
	 */
	public String getReason() {
		return reason;
	}
}
