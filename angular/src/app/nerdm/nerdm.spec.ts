import * as nerdm from './nerdm';
import { testdata } from '../../environments/environment';

import * as _ from 'lodash-es';

describe('NERDResource', function() {
    it("constructor", function() {
        let nrd = new nerdm.NERDResource(testdata['test4']);
        expect(nrd.data).toBeDefined();
        expect(nrd.data['@id']).toBe("ark:/88434/mds0000fbk4");
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
        let nrd1 = testdata['test1'];
        nrd1["@type"][0] = "nrdp:PublicDataResource";
        expect(nerdm.NERDResource._striptypes(nrd1)).toEqual(["PublicDataResource"]);
        expect(nerdm.NERDResource._striptypes(nrd1, "@type")).toEqual(["PublicDataResource"]);
        expect(nerdm.NERDResource._striptypes(nrd1, "goob")).toEqual([]);
        expect(nerdm.NERDResource._striptypes(nrd1['components'][1])).toEqual(["DataFile","Distribution"]);

        expect(nerdm.NERDResource._striptypes({'@type': "goob"})).toEqual(["goob"]);
        expect(nerdm.NERDResource._striptypes({'@type': ["ns:gurn", "goob"]})).toEqual(["goob","gurn"]);

        expect(nerdm.NERDResource._striptypes({'@type': "goob",
                                               'mytype': "gurn" },"mytype")).toEqual(["gurn"]);
    });

    it("_typesintersect", function() {
        let nrd1 = testdata['test1'];
        nrd1["@type"][0] = "nrdp:PublicDataResource";
        expect(nerdm.NERDResource._typesintersect(nrd1, ["PublicDataResource"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(nrd1, ["PublicDataResource"], "@type")).toBe(true);
        expect(nerdm.NERDResource._typesintersect(nrd1, ["PublicDataResource"], "keyword")).toBe(false);
        expect(nerdm.NERDResource._typesintersect(nrd1, ["face","hand"], "keyword")).toBe(true);
        expect(nerdm.NERDResource._typesintersect(nrd1, ["foot","hand"], "keyword")).toBe(false);

        expect(nerdm.NERDResource._typesintersect(nrd1, ["SRD"])).toBe(false);
        let cmp = nrd1['components'][1];
        expect(nerdm.NERDResource._typesintersect(cmp, ["SRD"])).toBe(false);
        expect(nerdm.NERDResource._typesintersect(cmp, ["DataFile","Gurn","SRD"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(cmp, ["DataFile","Distribution"])).toBe(true);
        expect(nerdm.NERDResource._typesintersect(cmp, ["Hank","Gurn","SRD"])).toBe(false);
        cmp = nrd1['components'][0];
        expect(nerdm.NERDResource._typesintersect(cmp, ["AKA","Hidden","Distribution"])).toBe(true);
        cmp = nrd1['components'][2];
        expect(nerdm.NERDResource._typesintersect(cmp, ["AKA","Hidden","ZZZ"])).toBe(false);
    });

    it("objectMatchesType", function() {
        let nrdtest2 = testdata['test1'];
        nrdtest2["@type"][0] = "nrdp:PublicDataResource";
        expect(nerdm.NERDResource.objectMatchesTypes(nrdtest2, ["PublicDataResource"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(nrdtest2, ["SRD"])).toBe(false);
        let cmp = nrdtest2['components'][1];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["SRD"])).toBe(false);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["DataFile","Gurn","SRD"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Gurn","SRD","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["SRD","Gurn","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["DataFile","Distribution"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Distribution","DataFile"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["Hank","Gurn","SRD"])).toBe(false);
        cmp = nrdtest2['components'][0];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["AKA","Hidden","Distribution"])).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, "Hidden")).toBe(true);
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, "ZZZ")).toBe(false);
        expect(nerdm.NERDResource.objectMatchesTypes(nrdtest2['contactPoint'], ["ZZZ"])).toBe(false);
        cmp = nrdtest2['components'][2];
        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["ZZZ","AKA","Hidden"])).toBe(false);

        expect(nerdm.NERDResource.objectMatchesTypes(cmp, ["ZZZ","AKA","Hidden"])).toBe(false);
    });

    it("getComponentsByType", () => {
        let nrd1 = new nerdm.NERDResource(testdata['test1']);
        nrd1.data["@type"][0] = "nrdp:PublicDataResource";

        let cmps : any[] = nrd1.getComponentsByType("DataFile");
        expect(cmps.length).toEqual(2);
        expect(cmps[0]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd1.getComponentsByType("nrdm:Hidden");
        expect(cmps.length).toEqual(1);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);

        cmps = nrd1.getComponentsByType(["Hidden", "nrdm:DataFile"]);
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[2]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd1.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['@type']).toEqual(["nrdp:Hidden", "nrdp:AccessPage", "dcat:Distribution"]);
        expect(cmps[1]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);
        expect(cmps[2]['@type']).toEqual(["nrdp:DataFile", "dcat:Distribution"]);

        cmps = nrd1.getComponentsByType("Goob");
        expect(cmps.length).toEqual(0);

        let nrdd = _.cloneDeep(testdata['test1']);
        nrdd["@type"] = "nrdp:PublicDataResource";

        nrdd['components'] = []
        nrd1 = new nerdm.NERDResource(nrdd);
        cmps = nrd1.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(0);
        delete nrd1.data['components'];
        expect(nrd1.data['components']).not.toBeDefined()
        cmps = nrd1.getComponentsByType(["Distribution"]);
        expect(cmps.length).toEqual(0);
    });

    it("countComponentsByType", () => {
        let nrd1 = new nerdm.NERDResource(testdata['test1']);
        expect(nrd1.countComponentsByType("DataFile")).toEqual(2);
    });

    it("getFilecListComponents", () => {
        let nrd2 = new nerdm.NERDResource(testdata['test2']);
        nrd2.data["@type"][0] = "nrdp:PublicDataResource";

        expect(nrd2.data['components'].length).toEqual(5);

        let cmps : any[] = nrd2.getFileListComponents();
        expect(cmps.length).toEqual(3);
        expect(cmps[0]['filepath']).toEqual("README.txt");
        expect(cmps[1]['filepath']).toEqual("data");
        expect(cmps[2]['filepath']).toEqual("data/file.csv");
    });

    it("countFilecListComponents", () => {
        let nrd2 = new nerdm.NERDResource(testdata['test2']);
        nrd2.data["@type"][0] = "nrdp:PublicDataResource";

        expect(nrd2.data['components'].length).toEqual(5);
        expect(nrd2.countFileListComponents()).toEqual(3);
    });

    it("getReferencesByType", () => {
        let nrd1 = new nerdm.NERDResource(testdata['test1']);
        nrd1.data["@type"][0] = "nrdp:PublicDataResource";
        nrd1.data["references"][0]["refType"] = "IsDocumentedBy";

        let refs : any[] = nrd1.getReferencesByType(["IsReferencedBy","IsDocumentedBy"]);
        expect(refs.length).toBe(1);
        expect(refs[0].refType).toBe("IsDocumentedBy");

        refs = nrd1.getReferencesByType(["IsSupplementTo","IsReferencedBy"]);
        expect(refs.length).toBe(0);
    });

    it("getPrimaryReferences", () => {
        let nrd1 = new nerdm.NERDResource(testdata['test1']);
        nrd1.data["@type"][0] = "nrdp:PublicDataResource";

        let refs : any[] = nrd1.getPrimaryReferences();
        expect(refs.length).toBe(1);
        expect(refs[0]['refType']).toBe("IsDocumentedBy");

        nrd1.data.references[0]['refType'] = "IsSupplementTo"
        refs = nrd1.getPrimaryReferences();
        expect(refs.length).toBe(1);
        expect(refs[0]['refType']).toBe("IsSupplementTo");

        nrd1.data['references'][0]['refType'] = "IsReferencedBy"
        refs = nrd1.getPrimaryReferences();
        expect(refs.length).toBe(0);
    });

    it("getCitation", () => {
        let nrd2 = new nerdm.NERDResource(testdata['test2']);
        nrd2.data["@type"][0] = "nrdp:PublicDataResource";
        let cstr = nrd2.getCitation();
        expect(cstr.startsWith("Doe, John, Plant, Robert (2011), Test2, National Institute of Standards and Technology, https://doi.org/XXXXX/MMMMM (Accessed ")).toBe(true);
        // expect(cstr).toEqual("Doe, John, Plant, Robert (2011) Test2, National Institute of Standards and Technology, https://doi.org/XXXXX/MMMMM (Accessed ");

        nrd2 = new nerdm.NERDResource(testdata['test1']);
        cstr = nrd2.getCitation();
//        expect(cstr).toBe("Patricia Flanagan (2019), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");
        expect(cstr).toContain("Patricia Flanagan (2019), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");

        let nrd1 = new nerdm.NERDResource(_.cloneDeep(testdata['test1']));
        delete nrd1.data['contactPoint']['fn'];
        cstr = nrd1.getCitation();
        expect(cstr).toContain("National Institute of Standards and Technology (2019), Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32, National Institute of Standards and Technology, https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds (Accessed ");
    });

    it('resourceLabel', () => {
        let nrdl = new nerdm.NERDResource(testdata['test1']);
        nrdl.data['@type'][0] = "nrdp:DataPublication"
        expect(nrdl.resourceLabel()).toEqual("Data Publication")

        nrdl.data['@type'][0] = "nrd:SRD"
        expect(nrdl.resourceLabel()).toEqual("Standard Reference Data")

        nrdl.data['@type'][0] = "nrd:SRM"
        expect(nrdl.resourceLabel()).toEqual("Standard Reference Material")

        nrdl.data['@type'][0] = "nrdp:PublicDataResource"
        expect(nrdl.resourceLabel()).toEqual("Public Data Resource")

        nrdl.data['@type'][0] = "nrda:ScienceTheme"
        expect(nrdl.resourceLabel()).toEqual("Science Theme")
    });


    it('selectAccessPages()', () => {
        let nrd1 = new nerdm.NERDResource(testdata['test1']);

        let aps = nrd1.selectAccessPages();
        expect(aps.length).toBe(1);
        expect(aps[0]['accessURL']).toBeTruthy();
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
