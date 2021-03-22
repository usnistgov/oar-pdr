import { DataCart, DataCartItem, DataCartLookup, stringifyCart, parseCart, stringifyMD, parseMD } from './cart';
import { testdata } from '../../environments/environment';

let emptycoll: DataCartLookup = <DataCartLookup>{};
let fakecoll: DataCartLookup = {
    "goob/gurn": {
        key: "goob/gurn", filePath: "gurn", resId: "goob", downloadURL: "http://here"
    }
};
let fakecoll_json: string = JSON.stringify(fakecoll);

describe('stringify-parse', () => {
    it("empty cart", () => {
        expect(stringifyCart(emptycoll)).toEqual('{}');
        expect(parseCart(stringifyCart(emptycoll))).toEqual(emptycoll);
    });

    it("non-empty cart", () => {
        expect(stringifyCart(fakecoll)).toEqual(fakecoll_json);
        expect(parseCart(stringifyCart(fakecoll))).toEqual(fakecoll);
    });

    it("empty metadata", () => {
        expect(parseMD(null)).toBeNull();
    });

    it("non-empty metadata", () => {
        expect(stringifyMD({updated: 4000})).toEqual('{"updated":4000}');
        expect(parseMD(stringifyMD({updated: 4000}))).toEqual({updated: 4000});
    });
});

describe('DataCart', () => {

    let sample: DataCartLookup = null;

    beforeEach(() => {
        sample = <DataCartLookup>JSON.parse(JSON.stringify(fakecoll));
    });

    afterEach(() => {
        localStorage.clear();
        sessionStorage.clear();
    });

    it('constructor', () => {
        let dc = new DataCart("cart", sample);
        expect(dc.contents).toBe(sample);
        expect(dc.cartName).toEqual("cart");
        expect(dc._storage).toBe(localStorage);
    
        dc = new DataCart("all", sample, sessionStorage);
        expect(dc.contents).toBe(sample);
        expect(dc.cartName).toEqual("all");
        expect(dc._storage).toBe(sessionStorage);
    
        dc = new DataCart("bloob", sample, null);
        expect(dc.contents).toBe(sample);
        expect(dc.cartName).toEqual("bloob");
        expect(dc._storage).toBeNull;
    });

    it('openCart()', () => {
        let dc = DataCart.openCart("cart");
        expect(dc).not.toBeNull();

        localStorage.setItem("cart:cart", stringifyCart(sample));
        dc = DataCart.openCart("cart");
        expect(dc).not.toBeNull();
        expect(dc.cartName).toEqual("cart");
        expect(dc.contents).toEqual(sample);
        
        dc = DataCart.openCart("cart", sessionStorage);
        expect(dc).not.toBeNull();
    });

    it('createCart()', () => {
        let dc = DataCart.createCart("goob");
        expect(dc).not.toBeNull();
        expect(dc.contents).toEqual({});
        expect(dc.cartName).toEqual("goob");
        expect(localStorage.getItem("cart:goob")).toEqual("{}");

        expect(sessionStorage.getItem("cart:goob")).toBeNull();
        localStorage.clear();
        dc = DataCart.createCart("goob", sessionStorage)
        expect(sessionStorage.getItem("cart:goob")).toEqual("{}");
        expect(localStorage.getItem("cart:goob")).toBeNull();
    });

    it('save()', () => {
        let saves = 0;

        let dc = new DataCart("cart", {});
        expect(localStorage.getItem("cart:cart")).toBeNull();
        expect(dc.lastUpdated).toEqual(0);

        dc.watchForChanges((w) => { saves++; });
        expect(saves).toEqual(0);  // saves does not get initialized
        dc.save();
        expect(localStorage.getItem("cart:cart")).toEqual("{}");
        expect(dc.lastUpdated).toBeGreaterThan(0);
        expect(saves).toEqual(1);
        
        dc = new DataCart("cart", sample, sessionStorage);
        expect(sessionStorage.getItem("cart:cart")).toBeNull();
        expect(dc.lastUpdated).toEqual(0);
        dc.save();
        expect(sessionStorage.getItem("cart:cart")).toEqual(fakecoll_json);
        expect(localStorage.getItem("cart:cart")).toEqual('{}');
        expect(dc.lastUpdated).toBeGreaterThan(0);
    });

    it('_forget()', () => {
        let dc = DataCart.createCart("cart");
        expect(localStorage.getItem("cart:cart")).toEqual("{}");
        dc._forget();
        expect(localStorage.getItem("cart:cart")).toBeNull();
        dc.restore();
        expect(dc.contents).toEqual({});
        dc.save();
        expect(localStorage.getItem("cart:cart")).toEqual("{}");

        localStorage.setItem("cart:cart", stringifyCart(sample));
        dc = DataCart.openCart("cart");
        expect(dc.contents).toEqual(sample);
        dc._forget();
        expect(localStorage.getItem("cart:cart")).toBeNull();
        dc.save();
        expect(localStorage.getItem("cart:cart")).toEqual(fakecoll_json);
    });

    it('restore()', () => {
        window.addEventListener("storage", (ev) => { console.log("Detected store update to "+ev.key); });
        let dc = DataCart.createCart("cart");
        expect(localStorage.getItem("cart:cart")).toEqual("{}");
        localStorage.setItem("cart:cart", stringifyCart(sample));
        expect(dc.contents).toEqual({});
        dc.restore();
        expect(dc.contents).toEqual(sample);
    });

    it('_checkForUpdate()', () => {
        window.addEventListener("storage", (ev) => { console.log("Detected store update to "+ev.key); });
        let dc = DataCart.createCart("cart");
        expect(localStorage.getItem("cart:cart")).toEqual("{}");
        localStorage.setItem("cart:cart", stringifyCart(sample));
        expect(dc.contents).toEqual({});
        dc._checkForUpdate({ key: "cart:cart" });
        expect(dc.contents).toEqual({});   // because date was not updated
        localStorage.setItem("cart:cart.md", stringifyMD({updated: Date.now()}));
    });

    it('findFileById()', () => {
        sample["foo/bar/goo"] = { resId: "foo", filePath: "bar/goo", count: 3 };
        sample["foo/bar/good"] = { resId: "foo", filePath: "bar/good", count: 3 };
        sample["oops"] = { resId: "oops", filePath: "", count: 0 };

        let dc = new DataCart("fred", sample, null);
        expect(dc.findFileById("hank/fred")).not.toBeDefined();
        let file = dc.findFileById("goob/gurn");
        expect(file).toBeDefined();
        expect(file.resId).toEqual("goob");

        file = dc.findFileById("foo/bar/goo");
        expect(file).toBeDefined();
        expect(file.resId).toEqual("foo");
        expect(file.filePath).toEqual("bar/goo");
        expect(file.count).toEqual(3);

        file = dc.findFileById("oops");
        expect(file).toBeDefined();
        expect(file.resId).toEqual("oops");
        expect(file.filePath).toEqual("");
        expect(file.count).toEqual(0);
    });

    it('findFile()', () => {
        sample["foo/bar/goo"] = { resId: "foo", filePath: "bar/goo", count: 3 };
        sample["foo/bar/good"] = { resId: "foo", filePath: "bar/good", count: 3 };
        sample["oops"] = { resId: "oops", filePath: "", count: 0 };

        let dc = new DataCart("fred", sample, null);
        expect(dc.findFile("hank", "fred")).not.toBeDefined();
        let file = dc.findFile("goob", "gurn");
        expect(file).toBeDefined();
        expect(file.resId).toEqual("goob");

        file = dc.findFile("foo", "bar/goo");
        expect(file).toBeDefined();
        expect(file.resId).toEqual("foo");
        expect(file.filePath).toEqual("bar/goo");
        expect(file.count).toEqual(3);
    });

    it('findItem()', () => {
        sample["foo/bar/goo"] = { resId: "foo", filePath: "bar/goo", count: 3 };
        sample["foo/bar/good"] = { resId: "foo", filePath: "bar/good", count: 3 };
        sample["oops/"] = { resId: "oops", filePath: "", count: 0 };

        let dc = new DataCart("fred", sample, null);
        expect(dc.findItem({resId: "hank", filePath: "fred"})).not.toBeDefined();
        expect(dc.findItem({filePath: "fred"})).not.toBeDefined();
        let file = dc.findItem(sample["goob/gurn"]);
        expect(file).toBeDefined();
        expect(file.resId).toEqual("goob");

        file = dc.findItem(sample["foo/bar/goo"]);
        expect(file).toBeDefined();
        expect(file.resId).toEqual("foo");
        expect(file.filePath).toEqual("bar/goo");
        expect(file.count).toEqual(3);

        file = dc.findItem(sample["oops/"]);
        expect(file).toBeDefined();
        expect(file.resId).toEqual("oops");
        expect(file.filePath).toEqual("");
        expect(file.count).toEqual(0);
    });

    it('size()', () => {
        let dc = new DataCart("cart", sample);
        dc.save();
        expect(dc.size()).toEqual(1);

        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
        expect(dc.size()).toEqual(2);
       
        dc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here" });
        dc.addFile("oops", { filePath: "a", count: 0, downloadURL: "http://here" });
        expect(dc.size()).toEqual(4);
    });

    it('countFilesDownloaded()', () => {
        let dc = new DataCart("cart", sample);
        dc.save();
        expect(dc.size()).toEqual(1);
        expect(dc.countFilesDownloaded()).toEqual(0);

        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here", downloadStatus: "downloaded" });
        expect(dc.countFilesDownloaded()).toEqual(1);
       
        dc.addFile("foo", { filePath: "bar/good", downloadURL: "http://here", count: 3 });
        dc.addFile("oops", { filePath: "a", downloadStatus: "downloaded", downloadURL: "http://here", count: 0 });
        expect(dc.countFilesDownloaded()).toEqual(2);
    });


    it('addFile()', () => {
        let dc = DataCart.createCart("cart");
        expect(dc.size()).toEqual(0);
        expect(localStorage.getItem("cart:cart")).toEqual("{}");

        let dci: DataCartItem = dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" },
                                           false, true);
        expect(dci.key).toBeTruthy();
        expect(dc.size()).toEqual(1);
        expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
        let file = dc.findFile("foo", "bar/goo");
        expect(file['filePath']).toEqual("bar/goo");
        expect(file['resId']).toEqual("foo");
        expect(file['downloadStatus']).toEqual("");
        expect(file['downloadURL']).toEqual("http://here");
        expect(file['count']).toEqual(3);

        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" }, false, true);
        expect(dc.size()).toEqual(2);
        expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
        file = dc.findFile("foo", "bar/good");
        expect(file['filePath']).toEqual("bar/good");
        expect(file['resId']).toEqual("foo");
        expect(file['downloadStatus']).toEqual("");
        expect(file['downloadURL']).toEqual("http://here");
        expect(file['count']).toEqual(8);

        dc.addFile("foo", { filePath: "bar/goo", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" }, false, true);
        expect(dc.size()).toEqual(2);
        expect(parseCart(localStorage.getItem("cart:cart"))).toEqual(dc.contents);
        file = dc.findFile("foo", "bar/goo");
        expect(file['filePath']).toEqual("bar/goo");
        expect(file['resId']).toEqual("foo");
        expect(file['downloadStatus']).toEqual("downloaded");
        expect(file['downloadURL']).toEqual("http://here");
        expect(file['count']).toEqual(1);
    });

    it('markAsDownloaded()', () => {
        let dc = DataCart.createCart("cart");
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
        expect(dc.countFilesDownloaded()).toEqual(1);

        expect(dc.markAsDownloaded("goober", "and/the/peas")).toBeFalsy();
        expect(dc.countFilesDownloaded()).toEqual(1);

        expect(dc.markAsDownloaded("foo", "bar/goo")).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(2);
        expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");

        expect(dc.markAsDownloaded("gov", "hank")).toBeTruthy();
        expect(dc.markAsDownloaded("foo", "bar/goo")).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(3);
        expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloaded");

        expect(dc.markAsDownloaded("foo", "bar/good")).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(4);
        expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloaded");

        expect(dc.markAsDownloaded("gov", "hank", false)).toBeTruthy();
        expect(dc.markAsDownloaded("foo", "bar/goo", false)).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(2);
        expect(dc.findFile("foo", "bar/goo")['downloadStatus']).toEqual("");
        expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("");
    });

    it('updateFileStatusOf()', () => {
        let dc = DataCart.createCart("cart");
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });

        let udc = DataCart.createCart("user", null);
        udc.addFile("foo", { filePath: "bar/good", count: 3, downloadURL: "http://here" });
        udc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "unknown", downloadURL: "http://here" });
        udc.addFile("gov", { filePath: "hank", count: 8, downloadURL: "http://here" });

        // expect(dc.updateFileStatusOf(udc, false)).toBe(1);
        expect(dc.findFile("foo", "bar/good")['downloadStatus']).toEqual("");
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");
        expect(dc.findFile("foo", "bar/good")['inCart']).not.toBeDefined();
        expect(dc.findFile("gov", "fred")['inCart']).not.toBeDefined();
        expect(dc.findFile("gov", "hank")['inCart']).not.toBeDefined();
        
        udc = DataCart.createCart("user", null);
        udc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "unknown", downloadURL: "http://here" });
        udc.addFile("gov", { filePath: "hank", count: 8, downloadURL: "http://here" });

        // expect(dc.updateFileStatusOf(udc)).toBe(1);
        expect(dc.findFile("gov", "fred")['downloadStatus']).toEqual("downloaded");
        expect(dc.findFile("gov", "hank")['downloadStatus']).toEqual("downloading");
        expect(dc.findFile("gov", "fred")['inCart']).not.toBeDefined(true);
        expect(dc.findFile("gov", "hank")['inCart']).not.toBeDefined(true);
    });

    it('matchFiles()', () => {
        let dc = DataCart.createCart("cart");
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" });
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
        expect(dc.size()).toEqual(4);
        expect(dc.countFilesDownloaded()).toEqual(1);

        expect(dc.matchFiles("gov").length).toEqual(2);
        expect(dc.matchFiles("foo", "bar/goo").length).toEqual(1);
        expect(dc.matchFiles("foo", "bar").length).toEqual(2);
    });

    it('getSelected()', () => {
        let saves = 0;

        let dc = DataCart.createCart("cart");
        dc.watchForChanges((w) => { saves++; });
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" }, false, false);
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" }, true);
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
        expect(dc.size()).toEqual(4);
        expect(dc.countFilesDownloaded()).toEqual(1);
        expect(dc.getSelectedFiles().length).toEqual(1);
        expect(saves).toEqual(3);

        let sel = dc.getSelectedFiles();
        expect(sel.length).toEqual(1);
        expect(sel[0].resId).toEqual("gov");
        expect(sel[0].filePath).toEqual("fred");

        dc.setSelected("gov");
        expect(saves).toEqual(4);
        sel = dc.getSelectedFiles();
        expect(sel.length).toEqual(2);
        expect(sel[0].resId).toEqual("gov");
        expect(sel[1].resId).toEqual("gov");
        expect(sel[0].filePath).not.toEqual(sel[1].filePath);

        dc.setSelected("gov", '', true);
        expect(dc.getSelectedFiles().length).toEqual(0);
        expect(saves).toEqual(5);

        dc.setSelected("foo", "bar", false, false);
        expect(saves).toEqual(5);
        sel = dc.getSelectedFiles();
        expect(sel.length).toEqual(2);
        expect(sel[0].resId).toEqual("foo");
        expect(sel[1].resId).toEqual("foo");
        expect(sel[0].filePath.startsWith("bar/")).toBeTruthy();
        expect(sel[1].filePath.startsWith("bar/")).toBeTruthy();
        expect(sel[0].filePath).not.toEqual(sel[1].filePath);

        dc.setSelected("gov", "fred");
        expect(saves).toEqual(6);
        sel = dc.getSelectedFiles();
        expect(sel.length).toEqual(3);
        expect(sel[0].resId).toEqual("foo");
        expect(sel[1].resId).toEqual("foo");
        expect(sel[2].resId).toEqual("gov");
        expect(sel[2].filePath).toEqual("fred");

        dc.removeSelectedFiles();
        expect(saves).toEqual(7);
        expect(dc.size()).toEqual(1);
        expect(dc.countFilesDownloaded()).toEqual(0);
        expect(dc.getSelectedFiles().length).toEqual(0);
    });

    it('getDownloadedFiles()', () => {
        let saves = 0;

        let dc = DataCart.createCart("cart");
        dc.watchForChanges((w) => { saves++; });
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" }, false, false);
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" }, false, false);
        dc.addFile("gov", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
        expect(dc.size()).toEqual(4);
        expect(dc.countFilesDownloaded()).toEqual(1);
        expect(dc.getSelectedFiles().length).toEqual(0);
        expect(saves).toEqual(2)

        let sel = dc.getDownloadedFiles();
        expect(sel.length).toEqual(1);
        expect(sel[0].resId).toEqual("gov");
        expect(sel[0].filePath).toEqual("fred");

        expect(dc.setDownloadStatus("gov", "hank")).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(2);
        expect(saves).toEqual(3)
        sel = dc.getDownloadedFiles();
        expect(sel.length).toEqual(2);
        expect(sel[0].resId).toEqual("gov");
        expect(sel[0].filePath).toEqual("fred");
        expect(sel[1].resId).toEqual("gov");
        expect(sel[1].filePath).toEqual("hank");

        dc.removeDownloadedFiles();
        expect(dc.size()).toEqual(2);
        expect(dc.countFilesDownloaded()).toEqual(0);
        expect(saves).toEqual(4)

        expect(dc.setDownloadStatus("foo", "bar/goo", "downloading", false)).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(0);
        expect(saves).toEqual(4)
        expect(dc.findFile("foo", "bar/goo").downloadStatus).toEqual('downloading');
        expect(dc.setDownloadStatus("foo", "bar", "downloaded", false)).toBeFalsy();
        expect(dc.countFilesDownloaded()).toEqual(0);
        expect(saves).toEqual(4)
        expect(dc.findFile("foo", "bar/goo").downloadStatus).toEqual('downloading');
        expect(dc.setDownloadStatus("foo", "bar/good", "downloaded", false)).toBeTruthy();
        expect(dc.countFilesDownloaded()).toEqual(1);
        expect(saves).toEqual(4)
        expect(dc.findFile("foo", "bar/good").downloadStatus).toEqual('downloaded');

        dc.save();
        expect(saves).toEqual(5)
    });

    it('removeMatchingFiles()', () => {
        let saves = 0;

        let dc = DataCart.createCart("cart");
        dc.watchForChanges((w) => { saves++; });
        dc.addFile("foo", { filePath: "bar/goo", count: 3, downloadURL: "http://here" }, false, false);
        dc.addFile("foo", { filePath: "bar/good", count: 8, downloadURL: "http://here" }, false, false);
        dc.addFile("fab", { filePath: "fred", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("fab", { filePath: "frank", count: 1, downloadStatus: "downloaded", downloadURL: "http://here" });
        dc.addFile("gov", { filePath: "hank", count: 8, downloadStatus: "downloading", downloadURL: "http://here" });
        expect(dc.size()).toEqual(5);
        expect(dc.countFilesDownloaded()).toEqual(2);
        expect(dc.getSelectedFiles().length).toEqual(0);
        expect(saves).toEqual(3)

        expect(dc.matchFiles("foo", "ba").length).toBe(0);  
        dc.removeMatchingFiles("foo", "ba");  // does not match; no change
        expect(dc.size()).toEqual(5);
        expect(saves).toEqual(3)

        expect(dc.matchFiles("fab").length).toBe(2);  
        dc.removeMatchingFiles("fab");       // matches fred and frank
        expect(dc.size()).toEqual(3);
        expect(saves).toEqual(4)
        expect(dc.matchFiles("fab").length).toBe(0);  

        expect(dc.matchFiles("foo", "bar").length).toBe(2);  
        dc.removeMatchingFiles("foo", "bar");  // match foo/bar/*
        expect(dc.size()).toEqual(1);
        expect(saves).toEqual(5)
        expect(dc.matchFiles("foo", "bar").length).toBe(0);  
    });
})

