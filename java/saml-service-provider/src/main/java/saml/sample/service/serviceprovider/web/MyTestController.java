package saml.sample.service.serviceprovider.web;

import org.springframework.web.bind.annotation.GetMapping;
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
    public Map<String, String> getValue() {
        Map<String, String> response = new HashMap<>();
        response.put("data", "a chunk of data");
        return response;
    }
}