import * as cfg from "./config"
import * as cfgsvc from "./config.service"
import { TransferState, StateKey } from '@angular/platform-browser';
import * as ngenv from '../../environments/environment';

describe("config.service deepcopy", function() {

    let a = { a: 1, b: { bc: "1.3", bd: 1.4, be: [ 1, 2.2, "3G", { z: 25, y: "24" } ] }};
    let b = cfgsvc.deepCopy(a);

    it("equivalent but independent", function() {
        expect(b).toEqual(a);

        a.b.be[3]["x"] = "better";
        expect(b).not.toEqual(a);
        
        a.a = 2;
        a.b.bc = "hey";
        a.b.be[0] = "you!";
        expect(b).not.toEqual(a);
    });    
});

describe("config.service AngularEnvironmentConfigService", function() {
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();
    let svc = new cfgsvc.AngularEnvironmentConfigService(plid, ts);

    it("getConfig()", function() {
        let ac : cfg.AppConfig = svc.getConfig() as cfg.AppConfig;

        expect(ac instanceof cfg.AppConfig).toBe(true);
        expect(ac.status).toBe("Dev Version");
        expect(ac["mode"]).toBe("dev");
        expect(ac["source"]).toBe("angular-env");
    });
});

describe("config.service newConfigService", function() {

    it("angular-env", function() {
        let plid : Object = "browser";
        let ts = new TransferState();
        let svc = cfgsvc.newConfigService(plid, ts);

        expect(svc instanceof cfgsvc.ConfigService).toBe(true);
        expect(svc instanceof cfgsvc.AngularEnvironmentConfigService).toBe(true);

        let ac : cfg.AppConfig = svc.getConfig() as cfg.AppConfig;
        expect(ac instanceof cfg.AppConfig).toBe(true);
        expect(ac.status).toBe("Dev Version");
        expect(ac["mode"]).toBe("dev");
        expect(ac["source"]).toBe("angular-env");
    });

    it("browser: transfer-state", function() {
        let plid : Object = "browser";
        
        let data : cfg.LPSConfig = cfgsvc.deepCopy(ngenv.config);
        data["mode"] = "prod";
        data['APIs'] = {
            "resolver": "goob",
            "serverSide": {
                "resolver": "gurn"
            }
        }
        let ts = new TransferState();
        ts.set(cfgsvc.CONFIG_TS_KEY, data);
        
        let svc = cfgsvc.newConfigService(plid, ts);

        expect(svc instanceof cfgsvc.ConfigService).toBe(true);
        expect(svc instanceof cfgsvc.TransferStateConfigService).toBe(true);

        let ac : cfg.AppConfig = svc.getConfig() as cfg.AppConfig;
        expect(ac instanceof cfg.AppConfig).toBe(true);
        expect(ac.status).toBe("Dev Version");
        expect(ac["mode"]).toBe("prod");
        expect(ac["source"]).toBe("transfer-state");
        expect(ac.get("APIs.resolver")).toBe("goob");
        expect(ac.get("APIs.serverSide")).not.toBeUndefined();
    });

    it("server: pre-loaded", function() {
        let plid : Object = "server";
        
        let data : cfg.LPSConfig = cfgsvc.deepCopy(ngenv.config);
        data["mode"] = "prod";
        data['APIs'] = {
            "resolver": "goob",
            "serverSide": {
                "resolver": "gurn"
            }
        }
        let ts = new TransferState();
        
        let svc = cfgsvc.newConfigService(plid, ts, data);

        expect(svc instanceof cfgsvc.ConfigService).toBe(true);
        expect(svc instanceof cfgsvc.ServerLoadedConfigService).toBe(true);

        let ac : cfg.AppConfig = svc.getConfig() as cfg.AppConfig;
        expect(ac instanceof cfg.AppConfig).toBe(true);
        expect(ac.status).toBe("Dev Version");
        expect(ac.get("APIs.resolver")).toBe("gurn");
        expect(ac.get("APIs.serverSide")).toBeUndefined();

        let saved = ts.get(cfgsvc.CONFIG_TS_KEY, null);
        expect(saved instanceof cfg.AppConfig).toBe(true);
        expect(saved.get("APIs.resolver")).toBe("goob");
        expect(saved.get("APIs.serverSide")).toBeUndefined();
    });

});

