package gov.nist.oar.customizationapi.config.JWTConfig;


import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import org.joda.time.DateTime;
import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.CredentialsExpiredException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.test.context.junit4.SpringRunner;

/**
 * @author 
 */
@RunWith(SpringRunner.class)
public class JWTAuthenticationProviderTest {
	String JWT_SECRET = "fmsgsnf#$%jsfhghsfdjjh#$%#$%^%^%$bhsfhsh";

    @Test
    public void supportsShouldReturnFalse() {
        JWTAuthenticationProvider JWTAuthenticationProvider = new JWTAuthenticationProvider(JWT_SECRET);
        Assert.assertFalse(JWTAuthenticationProvider.supports(UsernamePasswordAuthenticationToken.class));
    }

    @Test
    public void supportsShouldReturnTrue() {
        JWTAuthenticationProvider JWTAuthenticationProvider = new JWTAuthenticationProvider(JWT_SECRET);
        Assert.assertFalse(JWTAuthenticationProvider.supports(JWTAuthenticationFilter.class));
    }

    @Test
    public void shouldAuthenticate() {
        final JWTAuthenticationProvider JWTAuthenticationProvider = new JWTAuthenticationProvider(JWT_SECRET);
        final JWTAuthenticationToken JWTAuthenticationToken = new JWTAuthenticationToken(getJWT(120));
        Authentication authentication = JWTAuthenticationProvider.authenticate(new JWTAuthenticationToken(JWTAuthenticationToken));
        Assert.assertTrue(authentication.isAuthenticated());
    }

    @Test(expected = CredentialsExpiredException.class)
    public void shouldFailOnExpiredToken() {
        final JWTAuthenticationProvider JWTAuthenticationProvider = new JWTAuthenticationProvider(JWT_SECRET);
        final JWTAuthenticationToken JWTAuthenticationToken = new JWTAuthenticationToken(getJWT(-120));
        JWTAuthenticationProvider.authenticate(new JWTAuthenticationToken(JWTAuthenticationToken));
    }

    @Test(expected = BadCredentialsException.class)
    public void shouldFailOnBadSignature() {
        final JWTAuthenticationProvider JWTAuthenticationProvider = new JWTAuthenticationProvider(JWT_SECRET);

        String jwt = getJWT(120);
        int signIndex = jwt.lastIndexOf('.');
        jwt = jwt.substring(0, signIndex) + ".123456";

        final JWTAuthenticationToken JWTAuthenticationToken = new JWTAuthenticationToken(jwt);
        JWTAuthenticationProvider.authenticate(new JWTAuthenticationToken(JWTAuthenticationToken));
    }

    private String getJWT(int duration) {

        final DateTime dateTime = DateTime.now();

        JWTClaimsSet.Builder jwtClaimsSetBuilder = new JWTClaimsSet.Builder();
        jwtClaimsSetBuilder.expirationTime(dateTime.plusMinutes(duration).toDate());
        jwtClaimsSetBuilder.claim("APP", "SAMPLE");

        SignedJWT signedJWT = new SignedJWT(new JWSHeader(JWSAlgorithm.HS256), jwtClaimsSetBuilder.build());
        try {
            signedJWT.sign(new MACSigner(JWT_SECRET));
        } catch (JOSEException e) {
            throw new IllegalStateException(e);
        }

        return signedJWT.serialize();
    }

}