import * as mdt from './metadatatransfer-server.module';
import { NerdmRes, MetadataTransfer } from './nerdm';
import { AppConfig } from '../config/config';
import { SchemaLabel, NerdmConversionService } from './nerdmconversion.service';
import { config, testdata } from '../../environments/environment';

describe('serializeMetadataTransferFactory', function() {

    let doc : Document;
    let mdtrx : MetadataTransfer;
    let appcfg : AppConfig;

    beforeEach(() => {
        doc = new Document();
        doc = doc.implementation.createHTMLDocument();
        mdtrx = new MetadataTransfer();
        mdtrx.set("boring", {
            "@id": "boring",
            "@context": "https://intel.org",
            title: "All about me!",
            ediid: "123456",
            description: ["Dummy dummy."],
            keyword: ['keyword01'],
            accessLevel: "Public"
        });

        let cfg = JSON.parse(JSON.stringify(config));
        cfg['embedMetadata'] = [SchemaLabel.SCHEMA_ORG];
        appcfg = new AppConfig(cfg);
    });

    it('assumptions', function() {
        expect(doc.body).not.toBeNull();
        expect(doc.head).not.toBeNull();
        expect(doc.head.getElementsByTagName("script").length).toEqual(0);
    });

    it('add Nerdm only', function() {
        expect(doc.head.getElementsByTagName("script").length).toEqual(0);

        mdt.serializeMetadataTransferFactory(doc, mdtrx)();
        let scripts: any = doc.head.getElementsByTagName("script");
        expect(scripts.length).toEqual(1);
        scripts = doc.head.getElementsByClassName('structured-data');
        expect(scripts.length).toEqual(1);
        // console.log("el1", el);
        
        expect(scripts[0].tagName).toBe("SCRIPT");
        expect(scripts[0].getAttribute("id")).toBe("NERDm#Resource:boring");
        expect(scripts[0].getAttribute("type")).toBe("application/ld+json");
        expect(scripts[0].getAttribute("class")).toBe("structured-data NERDm Resource");

        let el_content = JSON.parse(scripts[0].textContent);
        // console.log("el_content", el_content);
        expect(el_content['@context']).toEqual("https://intel.org");
        expect(el_content['@id']).toEqual("boring");
        expect(el_content['title']).toEqual("All about me!");
        expect(el_content['ediid']).toEqual("123456");
        expect(el_content['description']).toEqual(["Dummy dummy."]);
        expect(el_content['accessLevel']).toEqual("Public");
        expect(el_content['keyword']).toEqual(["keyword01"]);
    });

    it('add Nerdm with schema.org', function() {
        expect(doc.head.getElementsByTagName("script").length).toEqual(0);

        let cvtr = new NerdmConversionService(appcfg);
        cvtr.supportConversion("scare", (md: NerdmRes): string => { return "boo!"; }, "text/word");
        cvtr.addFormatToEmbed("scare");

        mdt.serializeMetadataTransferFactory(doc, mdtrx, cvtr)();
        let script: any = doc.head.getElementsByTagName("script");
        expect(script.length).toEqual(3);
        script = doc.head.getElementsByClassName('structured-data');
        expect(script.length).toEqual(3);

        script = doc.head.getElementsByClassName("NERDm");
        expect(script.length).toEqual(1);
        script = script[0];
        expect(script).not.toBeNull();
        expect(script.getAttribute("id")).toEqual("NERDm#Resource:boring");
        expect(script.getAttribute("type")).toEqual("application/ld+json");
        expect(script.getAttribute("class")).toEqual("structured-data NERDm Resource");

        let el_content = JSON.parse(script.textContent);
        expect(el_content['@id']).toEqual("boring");
        expect(el_content['title']).toEqual("All about me!");
        expect(el_content['ediid']).toEqual("123456");
        expect(el_content['description']).toEqual(["Dummy dummy."]);

        script = doc.head.getElementsByClassName("schema.org");
        expect(script.length).toEqual(1);
        script = script[0];
        expect(script).not.toBeNull();
        expect(script.getAttribute("id")).toEqual("schema.org:boring");
        expect(script.getAttribute("type")).toEqual("application/ld+json");
        expect(script.getAttribute("class")).toEqual("structured-data schema.org");

        el_content = JSON.parse(script.textContent);
        expect(el_content['@context']).toEqual("https://schema.org");
        expect(el_content['@type']).toEqual("Dataset");
        expect(el_content['about']).toContain("boring");
        expect(el_content['name']).toEqual("All about me!");
        expect(el_content['description']).toEqual("Dummy dummy.");
        expect(el_content.citation).toBeTruthy();
        expect(el_content.url).toEqual("https://data.nist.gov/od/id/123456");

        script = doc.head.getElementsByClassName("scare");
        expect(script.length).toEqual(1);
        script = script[0];
        expect(script).not.toBeNull();
        expect(script.getAttribute("id")).toEqual("scare:boring");
        expect(script.getAttribute("type")).toEqual("text/word");
        expect(script.getAttribute("class")).toEqual("structured-data scare");
        expect(script.textContent).toEqual("boo!");
    });

    it('resists XSS/injection attacks', function() {
        let id = 'gotcha">null</scripts>Help!<scripts id="'
        mdtrx = new MetadataTransfer();
        mdtrx.set(id, { title: "All about me!" });

        expect(doc.head.getElementsByTagName("script").length).toEqual(0);
        mdt.serializeMetadataTransferFactory(doc, mdtrx)();
        let scripts: any = doc.head.getElementsByTagName("script");
        expect(scripts.length).toEqual(1);

        let el = scripts[0];
        let idatt = el.getAttribute("id");
        // console.log("TESTING: metadata saved with id='"+idatt+"'");
        expect(idatt).not.toEqual(id);
        expect(idatt.includes(">")).not.toBe(true);
        expect(idatt.includes("<")).not.toBe(true);
        expect(idatt.includes('"')).not.toBe(true);
        expect(idatt.includes("&")).toBe(true);
    });
});
