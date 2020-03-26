import * as nerdm from './nerdm';
import { testdata } from '../../environments/environment';

import * as _ from 'lodash';

describe('NERDResource', function() {

    it("constructor", function() {
        let nrd = new nerdm.NERDResource(testdata['test1']);
        expect(nrd.data).toBeDefined();
        expect(nrd.data['@id']).toBe("ark:/88434/mds0000fbk");
    });

    it("_isstring", function() {
        expect(nerdm.NERDResource._isstring("")).toBe(true);
        expect(nerdm.NERDResource._isstring("goob")).toBe(true);
        expect(nerdm.NERDResource._isstring(new String("goob"))).toBe(true);

        expect(nerdm.NERDResource._isstring(14)).toBe(false);
        expect(nerdm.NERDResource._isstring(["goob"])).toBe(false);
        expect(nerdm.NERDResource._isstring({"goob": "gurn"})).toBe(false);
    });

    it("_stripns", function() {
        expect(nerdm.NERDResource._stripns("")).toBe("");
        expect(nerdm.NERDResource._stripns("hank")).toBe("hank");
        expect(nerdm.NERDResource._stripns("nrd:hank")).toBe("hank");
        expect(nerdm.NERDResource._stripns("nrd:hank:gaherd")).toBe("hank:gaherd");
    });

    it("_striptypes", function() {
        let nrd = testdata['test1']
        expect(nerdm.NERDResource._striptypes(nrd)).toEqual(["PublicDataResource"]);
        expect(nerdm.NERDResource._striptypes(nrd['components'][1])).toEqual(["DataFile","Distribution"]);
        expect(nerdm.NERDResource._striptypes({'@type': "goob"})).toEqual(["goob"]);
        expect(nerdm.NERDResource._striptypes({'@type': ["ns:gurn", "goob"]})).toEqual(["goob","gurn"]);
    });

    it("_typesintersect", function() {
        let nrd = testdata['test1']
        expect(nerdm.NERDResource._typesintersect(nrd, ["PublicDataResource"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(nrd, ["SRD"])).toBe(false);
        let cmp = nrd['components'][1];
        expect(nerdm.NERDResource._typesintersect(cmp, ["SRD"])).toBe(false);
        expect(nerdm.NERDResource._typesintersect(cmp, ["DataFile","Gurn","SRD"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(cmp, ["DataFile","Distribution"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(cmp, ["Hank","Gurn","SRD"])).toBe(false);
        cmp = nrd['components'][0];
        expect(nerdm.NERDResource._typesintersect(cmp, ["AKA","Hidden","Distribution"])).toBe(true);
        cmp = nrd['components'][2];
        expect(nerdm.NERDResource._typesintersect(cmp, ["AKA","Hidden","ZZZ"])).toBe(false);
    });

    it("objectMatchesType", function() {
        let nrd = testdata['test1']
        expect(nerdm.NERDResource.objectMatchesTypes(nrd, ["PublicDataResource"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(nrd, ["SRD"])).toBe(false);
        let cmp = nrd['components'][1];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["SRD"])).toBe(false);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["DataFile","Gurn","SRD"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Gurn","SRD","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["SRD","Gurn","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["DataFile","Distribution"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Distribution","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Hank","Gurn","SRD"])).toBe(false);
        cmp = nrd['components'][0];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["AKA","Hidden","Distribution"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, "Hidden")).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, "ZZZ")).toBe(false);
        expect(nerdm.NERDResource.objectMatchesTypes(nrd['contactPoint'], ["ZZZ"])).toBe(false);
        cmp = nrd['components'][2];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["ZZZ","AKA","Hidden"])).toBe(false);

        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["ZZZ","AKA","Hidden"])).toBe(false);
    });

    it("getComponentsByType", () => {
        let nrd = new nerdm.NERDResource(testdata['test1']);
        let cmps : any[] = nrd.getComponentsByType("DataFile");
        expect(cmps.length).toEqual(2);
        expect(cmps[0]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd.getComponentsByType("nrdm:Hidden");
        expect(cmps.length).toEqual(1);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);

        cmps = nrd.getComponentsByType(["Hidden", "nrdm:DataFile"]);
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[2]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[2]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd.getComponentsByType("Goob");
        expect(cmps.length).toEqual(0);

        let nrdd = _.cloneDeep(testdata['test1']);
        nrdd['components'] = []
        nrd = new nerdm.NERDResource(nrdd);
        cmps = nrd.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(0);
        delete nrd.data['components'];
        expect(nrd.data['components']).not.toBeDefined()
        cmps = nrd.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(0);
    });

    it("countComponentsByType", () => {
        let nrd = new nerdm.NERDResource(testdata['test1']);
        expect(nrd.countComponentsByType("DataFile")).toEqual(2);
    });

    it("getFilecListComponents", () => {
        let nrd = new nerdm.NERDResource(testdata['test2']);
        expect(nrd.data['components'].length).toEqual(5);

        let cmps : any[] = nrd.getFileListComponents();
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['filepath']).toEqual("README.txt");
        expect(cmps[1]['filepath']).toEqual("data");
        expect(cmps[2]['filepath']).toEqual("data/file.csv");
    });

    it("countFilecListComponents", () => {
        let nrd = new nerdm.NERDResource(testdata['test2']);
        expect(nrd.data['components'].length).toEqual(5);
        expect(nrd.countFileListComponents()).toEqual(3);
    });

    it("getCitation", () => {
        let nrd = new nerdm.NERDResource(testdata['test2']);
        let cstr = nrd.getCitation();
        expect(cstr.startsWith("Doe, John, Plant, Robert (2011), Test2, National Institute of Standards and Technology, https://doi.org/XXXXX/MMMMM (Accessed ")).toBe(true);
        // expect(cstr).toEqual("Doe, John, Plant, Robert (2011) Test2, National Institute of Standards and Technology, https://doi.org/XXXXX/MMMMM (Accessed ");

        nrd = new nerdm.NERDResource(testdata['test1']);
        cstr = nrd.getCitation();
//        expect(cstr).toBe("Patricia Flanagan (2011), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");
        expect(cstr).toContain("Patricia Flanagan (2011), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");

        nrd = new nerdm.NERDResource(_.cloneDeep(testdata['test1']));
        delete nrd.data['contactPoint']['fn'];
        cstr = nrd.getCitation();
        expect(cstr).toContain("National Institute of Standards and Technology (2011), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");
    });
});

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
