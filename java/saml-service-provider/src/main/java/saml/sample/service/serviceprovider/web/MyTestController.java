package saml.sample.service.serviceprovider.web;

import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.HashMap;
import java.util.Map;

/**
 * @author 
 */
@RestController
@RequestMapping("/api/mycontroller")
public class MyTestController {

    @GetMapping
    public Map<String, String> getValue(@RequestHeader HttpHeaders headers) {
	System.out.println(headers.toString());
        Map<String, String> response = new HashMap<>();
        response.put("userId", headers.getFirst("userId"));
        //response.put("request header ", headers.get(0).get(0));
        return response;
    }
}