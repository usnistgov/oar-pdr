package gov.nist.oar.customizationapi.web;

import org.springframework.security.test.context.support.WithSecurityContext;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;


@Retention(RetentionPolicy.RUNTIME)
@WithSecurityContext(factory = WithMockSamlSecurityContextFactory.class)
public @interface WithMockSaml {

    String samlAssertFile();
}