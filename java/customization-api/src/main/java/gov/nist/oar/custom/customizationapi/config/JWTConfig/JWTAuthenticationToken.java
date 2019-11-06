package gov.nist.oar.custom.customizationapi.config.JWTConfig;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;

import java.util.Collection;

/**
 * This class represents authentication object, which is used to generate token.
 * @author Deoyani Nandrekar-Heinis
 */
public class JWTAuthenticationToken extends AbstractAuthenticationToken {

    private static final long serialVersionUID = -2848934719411152299L;
   
    private final transient Object principal;

    public JWTAuthenticationToken(Object principal) {
        super(null);
        this.principal=principal;
    }

    public JWTAuthenticationToken(Object principal, Object details, Collection<? extends GrantedAuthority> authorities) {
        super(authorities);
        this.principal = principal;
        super.setDetails(details);
        super.setAuthenticated(true);
    }

    @Override
    public Object getCredentials() {
        return "";
    }

    @Override
    public Object getPrincipal() {
        return principal;
    }
}