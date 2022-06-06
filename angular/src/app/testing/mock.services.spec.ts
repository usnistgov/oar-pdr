import { ParamMap } from '@angular/router';
import { ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import * as rxjs from 'rxjs';
import * as mocksv from './mock.services';

describe('SimpleParamMap', function() {
    let pm : ParamMap = null;

    it('empty constructor', function() {
        pm = new mocksv.SimpleParamMap();
        expect(pm.keys).toEqual([]);
        expect(pm.get('goober')).toBeNull();
        expect(pm.getAll('goober')).toBeNull();
    });

    it('constructor with inputs', function() {
        pm = new mocksv.SimpleParamMap({ id: "goober", title: "Me!"});
        expect(pm.keys).toEqual(["id", "title"]);
        expect(pm.get('id')).toEqual("goober");
        expect(pm.get('title')).toEqual("Me!");
        expect(pm.getAll('goober')).toBeNull();
    });
});

describe('MockActivatedRouteSnapshot', function() {
    it('construction', function() {
        let snapshot : mocksv.Map =
            new mocksv.MockActivatedRouteSnapshot("/goober;pid=w/hank", { id: "hank"}, {c: ["1", "2"]});

        expect(snapshot.url.length).toBe(3);
        expect(snapshot.url[0].path).toBe("");
        expect(snapshot.url[1].path).toBe("goober");
        expect(snapshot.url[2].path).toBe("hank");
        expect(snapshot.url[1].parameterMap.get("pid")).toBe("w");
        expect(snapshot.params["id"]).toBe("hank");
        expect(snapshot.paramMap.get("id")).toBe("hank");
        expect(snapshot.queryParams["c"]).toEqual(["1", "2"]);
    });
});

describe('MockActivatedRoute', function() {
    it('construction', function() {
        let route : mocksv.Map =
            new mocksv.MockActivatedRoute("/goober;pid=w/hank", { id: "hank"}, {c: ["1", "2"]});

        expect(route.snapshot.url.length).toBe(3);
        expect(route.snapshot.url[0].path).toBe("");
        expect(route.snapshot.url[1].path).toBe("goober");
        expect(route.snapshot.url[2].path).toBe("hank");
        expect(route.snapshot.url[1].parameterMap.get("pid")).toBe("w");
        expect(route.snapshot.params["id"]).toBe("hank");
        expect(route.snapshot.paramMap.get("id")).toBe("hank");
        expect(route.snapshot.queryParams["c"]).toEqual(["1", "2"]);
    });
});
