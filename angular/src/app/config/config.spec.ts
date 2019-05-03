import * as config from "./config";

describe("config.WebLocations", function() {

    it("WebLocations recognizes WebLocations instance data", function() {
        let data : config.WebLocations = {
            orgHome: "https://nist.gov/",  portalBase: "https://data.nist.gov/",
            author: "ray" };
        expect(data.portalBase).toBe("https://data.nist.gov/");
        expect(data.pdrHome).toBe(undefined);
        expect(data["author"]).toBe("ray");

        /*
        let wrong : config.WebLocations = { portalBase: "https://data.nist.gov/",
                                            author: "ray" };
        */
    });
});

describe("config.LPSConfig", function() {

    it("LPSConfig recognized LPSConfig instance data", function() {
        let data : config.LPSConfig = {
            locations: {
                orgHome: "https://nist.gov/",  portalBase: "https://data.nist.gov/"
            },
            appVersion: "1.1.0",
            author: "ray"
        }
            
        expect(data.locations.portalBase).toBe("https://data.nist.gov/");
        expect(data.status).toBe(undefined);
        expect(data["author"]).toBe("ray");
    });
});

describe("config.AppConfig", function() {

    it("Instance initialized from an LPSConfig instance", function() {
        let data : config.LPSConfig = {
            locations: {
                orgHome: "https://nist.gov/",  portalBase: "https://data.nist.gov/"
            },
            appVersion: "1.1.0",
            author: "ray"
        }
        let cfg : config.AppConfig = new config.AppConfig(data);

        expect(cfg.locations.portalBase).toBe("https://data.nist.gov/");
        expect(cfg["locations"].orgHome).toBe("https://nist.gov/");
        expect(cfg.status).toBe(undefined);
        expect(cfg["author"]).toBe("ray");

        // check for default values
        expect(cfg.editEnabled).toBeDefined();
        expect(cfg.editEnabled).toBe(false);
        expect(cfg.locations.pdrHome).toBeDefined();
        expect(cfg.locations.pdrHome).toBe("https://data.nist.gov/pdr/");
        expect(cfg.locations.pdrSearch).toBeDefined();
        expect(cfg.locations.pdrSearch).toBe("https://data.nist.gov/sdp/");
        expect(cfg.locations.distService).toBeDefined();
        expect(cfg.locations.distService).toBe("https://data.nist.gov/od/ds/");
        expect(cfg.locations.mdService).toBeDefined();
        expect(cfg.locations.mdService).toBe("https://data.nist.gov/rmm/");
        expect(cfg.locations.landingPageService).toBeDefined();
        expect(cfg.locations.landingPageService).toBe("https://data.nist.gov/od/id/");
        expect(cfg.locations.nerdmAbout).toBeDefined();
        expect(cfg.locations.nerdmAbout).toBe("https://data.nist.gov/od/dm/aboutNerdm.html");
        expect(cfg.mdAPI).toBeDefined();
        expect(cfg.mdAPI).toBe("https://data.nist.gov/rmm/");
    });

    it("get()", function() {
        let data : config.LPSConfig = {
            locations: {
                orgHome: "https://nist.gov/",  portalBase: "https://data.nist.gov/"
            },
            appVersion: "1.1.0",
            author: "ray"
        }
        let cfg : config.AppConfig = new config.AppConfig(data);

        expect(cfg.get("appVersion")).toBe("1.1.0");

        let author : string = cfg.get("author");
        expect(author).toBe("ray");
        author = cfg.get("author", "me!");
        expect(author).toBe("ray");

        expect(cfg["status"]).toBe(undefined);
        expect(cfg.get("status", "testing")).toBe("testing");
        cfg.status = null;
        expect(cfg.get("status", "testing")).toBe("testing");
        cfg.status = "review";
        expect(cfg.get("status", "testing")).toBe("review");

        expect(cfg.get("locations.orgHome", "nowhere")).toBe("https://nist.gov/");
        expect(cfg.get("locations.pdrSearch", "nowhere")).toBe("https://data.nist.gov/sdp/");
        expect(cfg.get("locations.hell")).toBe(undefined);
        expect(cfg.get("locations.hell", "nowhere")).toBe("nowhere");
    });
});
