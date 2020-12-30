import { DataCartStatus, DataCartStatusLookup, DataCartStatusItem, DataCartStatusData, stringifyCart, parseCartStatus } from './cartstatus';

let emptycoll: DataCartStatusLookup = <DataCartStatusLookup>{};
let fakecoll: DataCartStatusLookup = { "goob/gurn": { itemId: "gurn", statusData: {isInUse:true, downloadPercentage: 0} } };
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
        sample["foo/bar/goo"] = { itemId: "goo", statusData: {isInUse:true, downloadPercentage: 100} };
        sample["foo/bar/good"] = { itemId: "foo", statusData: {isInUse:true, downloadPercentage: 50} };
        sample["oops"] = { itemId: "oops", statusData: {isInUse:false, downloadPercentage: 0} };

        let dcs = new DataCartStatus("fred", sample, null);
        expect(dcs.findStatusById("hank/fred")).not.toBeDefined();
        let file = dcs.findStatusById("foo/bar/goo");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("goo");
        expect(file.statusData.isInUse).toBeTruthy();
        expect(file.statusData.downloadPercentage).toEqual(100);

        file = dcs.findStatusById("foo/bar/good");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("foo");
        expect(file.statusData.isInUse).toBeTruthy();
        expect(file.statusData.downloadPercentage).toEqual(50);

        file = dcs.findStatusById("oops");
        expect(file).toBeDefined();
        expect(file.itemId).toEqual("oops");
        expect(file.statusData.isInUse).toBeFalsy();
        expect(file.statusData.downloadPercentage).toEqual(0);
    });

    // it('findFile()', () => {
    //     sample["foo/bar/goo"] = { resId: "foo", filePath: "bar/goo", count: 3 };
    //     sample["foo/bar/good"] = { resId: "foo", filePath: "bar/good", count: 3 };
    //     sample["oops"] = { resId: "oops", filePath: "", count: 0 };

    //     let dc = new DataCart("fred", sample, null);
    //     expect(dc.findFile("hank", "fred")).not.toBeDefined();
    //     let file = dc.findFile("goob", "gurn");
    //     expect(file).toBeDefined();
    //     expect(file.resId).toEqual("goob");

    //     file = dc.findFile("foo", "bar/goo");
    //     expect(file).toBeDefined();
    //     expect(file.resId).toEqual("foo");
    //     expect(file.filePath).toEqual("bar/goo");
    //     expect(file.count).toEqual(3);
    // });

    // it('findItem()', () => {
    //     sample["foo/bar/goo"] = { resId: "foo", filePath: "bar/goo", count: 3 };
    //     sample["foo/bar/good"] = { resId: "foo", filePath: "bar/good", count: 3 };
    //     sample["oops/"] = { resId: "oops", filePath: "", count: 0 };

    //     let dc = new DataCart("fred", sample, null);
    //     expect(dc.findItem({resId: "hank", filePath: "fred"})).not.toBeDefined();
    //     expect(dc.findItem({filePath: "fred"})).not.toBeDefined();
    //     let file = dc.findItem(sample["goob/gurn"]);
    //     expect(file).toBeDefined();
    //     expect(file.resId).toEqual("goob");

    //     file = dc.findItem(sample["foo/bar/goo"]);
    //     expect(file).toBeDefined();
    //     expect(file.resId).toEqual("foo");
    //     expect(file.filePath).toEqual("bar/goo");
    //     expect(file.count).toEqual(3);

    //     file = dc.findItem(sample["oops/"]);
    //     expect(file).toBeDefined();
    //     expect(file.resId).toEqual("oops");
    //     expect(file.filePath).toEqual("");
    //     expect(file.count).toEqual(0);
    // });

    // it('size()', () => {
    //     let dc = new DataCart("cart", sample);
    //     dc.save();
    //     expect(dc.size()).toEqual(1);

    //     dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
    //     expect(dc.size()).toEqual(2);
       
    //     dc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here" });
    //     dc.addFile("oops", { filePath: "a", count: 0, downloadURL: "http://here" });
    //     expect(dc.size()).toEqual(4);
    // });

    // it('countFilesDownloaded()', () => {
    //     let dc = new DataCart("cart", sample);
    //     dc.save();
    //     expect(dc.size()).toEqual(1);
    //     expect(dc.countFilesDownloaded()).toEqual(0);

    //     dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here", downloadStatus: "downloaded" });
    //     expect(dc.countFilesDownloaded()).toEqual(1);
       
    //     dc.addFile("foo", { filePath: "bar/good", downloadURL: "http://here", count: 3 });
    //     dc.addFile("oops", { filePath: "a", downloadStatus: "downloaded", downloadURL: "http://here", count: 0 });
    //     expect(dc.countFilesDownloaded()).toEqual(2);
    // });


    // it('addFile()', () => {
    //     let dc = DataCart.createCart("cart");
    //     expect(dc.size()).toEqual(0);
    //     expect(localStorage.getItem("cart:cart")).toEqual("{}");

    //     dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
    //     expect(dc.size()).toEqual(1);
    //     expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
    //     let file = dc.findFile("foo", "bar/goo");
    //     expect(file['filePath']).toEqual("bar/goo");
    //     expect(file['resId']).toEqual("foo");
    //     expect(file['downloadStatus']).toEqual("");
    //     expect(file['downloadURL']).toEqual("http://here");
    //     expect(file['count']).toEqual(3);

    //     dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
    //     expect(dc.size()).toEqual(2);
    //     expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
    //     file = dc.findFile("foo", "bar/good");
    //     expect(file['filePath']).toEqual("bar/good");
    //     expect(file['resId']).toEqual("foo");
    //     expect(file['downloadStatus']).toEqual("");
    //     expect(file['downloadURL']).toEqual("http://here");
    //     expect(file['count']).toEqual(8);

    //     dc.addFile("foo", { filePath: "bar/goo", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
    //     expect(dc.size()).toEqual(2);
    //     expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
    //     file = dc.findFile("foo", "bar/goo");
    //     expect(file['filePath']).toEqual("bar/goo");
    //     expect(file['resId']).toEqual("foo");
    //     expect(file['downloadStatus']).toEqual("downloaded");
    //     expect(file['downloadURL']).toEqual("http://here");
    //     expect(file['count']).toEqual(1);
    // });

    // it('markAsDownloaded()', () => {
    //     let dc = DataCart.createCart("cart");
    //     dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
    //     dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
    //     dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
    //     dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
    //     expect(dc.countFilesDownloaded()).toEqual(1);

    //     expect(dc.markAsDownloaded("goober", "and/the/peas")).toBeFalsy();
    //     expect(dc.countFilesDownloaded()).toEqual(1);

    //     expect(dc.markAsDownloaded("foo", "bar/goo")).toBeTruthy();
    //     expect(dc.countFilesDownloaded()).toEqual(2);
    //     expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");

    //     expect(dc.markAsDownloaded("gov", "hank")).toBeTruthy();
    //     expect(dc.markAsDownloaded("foo", "bar/goo")).toBeTruthy();
    //     expect(dc.countFilesDownloaded()).toEqual(3);
    //     expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloaded");

    //     expect(dc.markAsDownloaded("foo", "bar/good")).toBeTruthy();
    //     expect(dc.countFilesDownloaded()).toEqual(4);
    //     expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloaded");

    //     expect(dc.markAsDownloaded("gov", "hank", false)).toBeTruthy();
    //     expect(dc.markAsDownloaded("foo", "bar/goo", false)).toBeTruthy();
    //     expect(dc.countFilesDownloaded()).toEqual(2);
    //     expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("");
    //     expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("");
    // });

    // it('updateFileStatusOf()', () => {
    //     let dc = DataCart.createCart("cart");
    //     dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
    //     dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
    //     dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
    //     dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });

    //     let udc = DataCart.createCart("user", null);
    //     udc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here" });
    //     udc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "unknown", downloadURL: "http://here" });
    //     udc.addFile("gov", { filePath: "hank", count: 8, downloadURL: "http://here" });

    //     // expect(dc.updateFileStatusOf(udc, false)).toBe(1);
    //     expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");
    //     expect(dc.findFile("foo", "bar/good")['inCart']).not.toBeDefined();
    //     expect(dc.findFile("gov", "fred")['inCart']).not.toBeDefined();
    //     expect(dc.findFile("gov", "hank")['inCart']).not.toBeDefined();
        
    //     udc = DataCart.createCart("user", null);
    //     udc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "unknown", downloadURL: "http://here" });
    //     udc.addFile("gov", { filePath: "hank", count: 8, downloadURL: "http://here" });

    //     // expect(dc.updateFileStatusOf(udc)).toBe(1);
    //     expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
    //     expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");
    //     expect(dc.findFile("gov", "fred")['inCart']).not.toBeDefined(true);
    //     expect(dc.findFile("gov", "hank")['inCart']).not.toBeDefined(true);
    // });
})

