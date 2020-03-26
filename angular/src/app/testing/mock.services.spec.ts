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
            new mocksv.MockActivatedRouteSnapshot("/goober/hank", { id: "hank"}, {c: ["1", "2"]});

        expect(snapshot.url.length).toBe(1);
        expect(snapshot.url[0].path).toBe("/goober/hank");
        expect(snapshot.url[0].parameterMap.get("id")).toBe("hank");
        expect(snapshot.params["id"]).toBe("hank");
        expect(snapshot.paramMap.get("id")).toBe("hank");
        expect(snapshot.queryParams["c"]).toEqual(["1", "2"]);
    });
});

describe('MockActivatedRoute', function() {
    it('construction', function() {
        let route : mocksv.Map =
            new mocksv.MockActivatedRoute("/goober/hank", { id: "hank"}, {c: ["1", "2"]});

        expect(route.snapshot.url.length).toBe(1);
        expect(route.snapshot.url[0].path).toBe("/goober/hank");
        expect(route.snapshot.url[0].parameterMap.get("id")).toBe("hank");
        expect(route.snapshot.params["id"]).toBe("hank");
        expect(route.snapshot.paramMap.get("id")).toBe("hank");
        expect(route.snapshot.queryParams["c"]).toEqual(["1", "2"]);
    });
});
