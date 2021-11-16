//package gov.nist.oar.customizationapi.web;
//
//import org.opensaml.saml2.core.Assertion;
//import org.opensaml.saml2.core.Attribute;
//import org.springframework.security.core.context.SecurityContext;
//import org.springframework.security.core.context.SecurityContextHolder;
//import org.springframework.security.providers.ExpiringUsernameAuthenticationToken;
//import org.springframework.security.saml.SAMLCredential;
//import org.springframework.security.test.context.support.WithSecurityContextFactory;
//
//import gov.nist.oar.customizationapi.util.SamlTestUtil;
//
//import java.util.ArrayList;
//
//public class WithMockSamlSecurityContextFactory implements WithSecurityContextFactory<WithMockSaml> {
//
//    @Override
//    public SecurityContext createSecurityContext(WithMockSaml withMockSaml) {
//
//        final SecurityContext context = SecurityContextHolder.createEmptyContext();
//        final Assertion assertion = SamlTestUtil.loadAssertion(withMockSaml.samlAssertFile());
//
//        final SAMLCredential samlCredential = new SAMLCredential(
//                assertion.getSubject().getNameID(),
//                assertion,
//                null,
//                new ArrayList<Attribute>(),
//                null);
//
//        ExpiringUsernameAuthenticationToken authentication =
//                new ExpiringUsernameAuthenticationToken(
//                        null,
//                        assertion.getSubject().getNameID(),
//                        samlCredential,
//                        null);
//
//        context.setAuthentication(authentication);
//
//        return context;
//    }
//}