import * as nerdm from './nerdm';

describe('MetadataTransfer', function() {

    let trx : nerdm.MetadataTransfer;

    beforeEach(() => {
        trx = new nerdm.MetadataTransfer();
    });

    it("constructor", function() {
        expect(trx.labels()).toEqual([]);
        expect(trx.isSet("goober")).toBeFalsy();
        expect(trx.get("goober")).toBeUndefined();
        expect(trx.serialize("goober")).toBe("");
    });

    it("get/set", function() {
        let data = { title: "All about Me!" }
        expect(trx.get("boring")).toBeUndefined();
        expect(trx.isSet("boring")).toBeFalsy();
        trx.set("boring", data);
        expect(trx.get("boring")).toEqual(data);
        expect(trx.isSet("boring")).toBeTruthy()
        expect(trx.labels()).toEqual(["boring"]);
        expect(trx.isSet("goober")).toBeFalsy();
        expect(trx.get("goober")).toBeUndefined();

        trx.set("snooze", { name: "Hank" })
        expect(trx.get("boring")).toEqual(data);
        expect(trx.get("snooze")["name"]).toBe("Hank");
        expect(trx.labels()).toEqual(["boring", "snooze"]);
    });

    it("serialize", function() {
        let data = { title: "All about cats!" }
        trx.set("boring", data);
        let out = trx.serialize("boring")
        expect(out.includes('"title":')).toBe(true);
        expect(out.startsWith('{')).toBe(true);
        expect(out.endsWith('}')).toBe(true);
        expect(JSON.parse(out)).toEqual(data);
    });
});
