import { DataCartStatus, DataCartStatusLookup, DataCartStatusItem, DataCartStatusData, stringifyCart, parseCartStatus } from './cartstatus';

let emptycoll: DataCartStatusLookup = <DataCartStatusLookup>{};
let fakecoll: DataCartStatusLookup = { "goob/gurn": { itemId: "gurn", displayName: "gurnDisplay", isInUse:true, downloadPercentage: 0 } };
let fakecoll_json: string = JSON.stringify(fakecoll);

describe('stringify-parse', () => {
    it("empty", () => {
        expect(stringifyCart(emptycoll)).toEqual('{}');
        expect(parseCartStatus(stringifyCart(emptycoll))).toEqual(emptycoll);
    });

    it("non-empty", () => {
        expect(stringifyCart(fakecoll)).toEqual(fakecoll_json);
        expect(parseCartStatus(stringifyCart(fakecoll))).toEqual(fakecoll);
    });
});

describe('DataCartStatus', () => {

    let sample: DataCartStatusLookup = null;

    beforeEach(() => {
        sample = <DataCartStatusLookup>JSON.parse(JSON.stringify(fakecoll));
    });

    afterEach(() => {
        localStorage.clear();
        sessionStorage.clear();
    });

    it('constructor', () => {
        let dcs = new DataCartStatus("cartStatus", sample);
        expect(dcs.dataCartStatusItems).toBe(sample);
        expect(dcs.name).toEqual("cartStatus");
        expect(dcs._storage).toBe(localStorage);
    
        dcs = new DataCartStatus("all", sample, sessionStorage);
        expect(dcs.dataCartStatusItems).toBe(sample);
        expect(dcs.name).toEqual("all");
        expect(dcs._storage).toBe(sessionStorage);
    
        dcs = new DataCartStatus("bloob", sample, null);
        expect(dcs.dataCartStatusItems).toBe(sample);
        expect(dcs.name).toEqual("bloob");
        expect(dcs._storage).toBeNull;
    });

    it('openCartStatus()', () => {
        let dcs = DataCartStatus.openCartStatus("cartStatus");
        expect(dcs).not.toBeNull();

        localStorage.setItem("cartStatus", stringifyCart(sample));
        dcs = DataCartStatus.openCartStatus("cartStatus");
        expect(dcs).not.toBeNull();
        expect(dcs.name).toEqual("cartStatus");
        expect(dcs.dataCartStatusItems).toEqual(sample);
        
        dcs = DataCartStatus.openCartStatus("cartStatus", sessionStorage);
        expect(dcs).not.toBeNull();
    });

    it('createCartStatus()', () => {
        let dcs = DataCartStatus.createCartStatus("goob");
        expect(dcs).not.toBeNull();
        expect(dcs.dataCartStatusItems).toEqual({});
        expect(dcs.name).toEqual("goob");
        expect(localStorage.getItem("goob")).toEqual("{}");

        expect(sessionStorage.getItem("goob")).toBeNull();
        localStorage.clear();
        dcs = DataCartStatus.createCartStatus("goob", sessionStorage)
        expect(sessionStorage.getItem("goob")).toEqual("{}");
        expect(localStorage.getItem("goob")).toBeNull();
    });

    it('save()', () => {
        let dcs = new DataCartStatus("cartStatus", {});
        expect(localStorage.getItem("cartStatus")).toBeNull();
        dcs.save();
        expect(localStorage.getItem("cartStatus")).toEqual("{}");
        
        dcs = new DataCartStatus("cartStatus", sample, sessionStorage);
        expect(sessionStorage.getItem("cartStatus")).toBeNull();
        dcs.save();
        expect(sessionStorage.getItem("cartStatus")).toEqual(fakecoll_json);
        expect(localStorage.getItem("cartStatus")).toEqual('{}');
    });

    it('forget()', () => {
        let dcs = DataCartStatus.createCartStatus("cartStatus");
        expect(localStorage.getItem("cartStatus")).toEqual("{}");
        dcs.forget();
        expect(localStorage.getItem("cartStatus")).toBeNull();
        dcs.save();
        expect(localStorage.getItem("cartStatus")).toEqual("{}");

        localStorage.setItem("cartStatus", stringifyCart(sample));
        dcs = DataCartStatus.openCartStatus("cartStatus");
        expect(dcs.dataCartStatusItems).toEqual(sample);
        dcs.forget();
        expect(localStorage.getItem("cartStatus")).toBeNull();
        dcs.save();
        expect(localStorage.getItem("cartStatus")).toEqual(fakecoll_json);
    });

    it('restore()', () => {
        let dcs = DataCartStatus.createCartStatus("cartStatus");
        expect(localStorage.getItem("cartStatus")).toEqual("{}");
        localStorage.setItem("cartStatus", stringifyCart(sample));
        expect(dcs.dataCartStatusItems).toEqual({});
        dcs.restore();
        expect(dcs.dataCartStatusItems).toEqual(sample);
    });

    it('findStatusById()', () => {
        sample["foo/bar/goo"] = { itemId: "goo", displayName: "gooDisplay", isInUse:true, downloadPercentage: 100 };
        sample["foo/bar/good"] = { itemId: "foo", displayName: "fooDisplay", isInUse:true, downloadPercentage: 50 };
        sample["oops"] = { itemId: "oops", displayName: "oopsDisplay", isInUse:false, downloadPercentage: 0 };

        let dcs = new DataCartStatus("fred", sample, null);
        expect(dcs.findStatusById("hank/fred")).not.toBeDefined();
        let file = dcs.findStatusById("foo/bar/goo");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("goo");
        expect(file.displayName).toEqual("gooDisplay");
        expect(file.isInUse).toBeTruthy();
        expect(file.downloadPercentage).toEqual(100);

        file = dcs.findStatusById("foo/bar/good");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("foo");
        expect(file.displayName).toEqual("fooDisplay");
        expect(file.isInUse).toBeTruthy();
        expect(file.downloadPercentage).toEqual(50);

        file = dcs.findStatusById("oops");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("oops");
        expect(file.displayName).toEqual("oopsDisplay");
        expect(file.isInUse).toBeFalsy();
        expect(file.downloadPercentage).toEqual(0);
    });
})

