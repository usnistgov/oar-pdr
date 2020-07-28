package gov.nist.oar.customizationapi.config.ServiceConfig;

import org.springframework.security.authentication.AbstractAuthenticationToken;

public class ServiceAuthToken extends AbstractAuthenticationToken {
	private static final long serialVersionUID = -2848934719411152299L;

	private final transient Object principal;

	public ServiceAuthToken(Object principal) {
		super(null);
		this.principal = principal;
	}

	@Override
	public Object getCredentials() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Object getPrincipal() {
		// TODO Auto-generated method stub
		return principal;
	}

}
