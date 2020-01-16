import * as mdt from './metadatatransfer-server.module';
import { MetadataTransfer } from './nerdm';

describe('serializeMetadataTransferFactory', function() {

    let doc : Document;
    let mdtrx : MetadataTransfer;

    beforeEach(() => {
        doc = new Document();
        doc = doc.implementation.createHTMLDocument();
        mdtrx = new MetadataTransfer();
        mdtrx.set("boring", { title: "All about me!" });
    });

    it('assumptions', function() {
        expect(doc.body).not.toBeNull();
        expect(doc.body.firstChild).toBeNull();
    });

    it('add to empty body', function() {
        expect(doc.body.firstElementChild).toBeNull();
        mdt.serializeMetadataTransferFactory(doc, mdtrx)();
        expect(doc.body.firstElementChild).not.toBeNull();
        let el = doc.body.firstElementChild;
        expect(el.tagName).toBe("SCRIPT");
        expect(el.getAttribute("id")).toBe("boring");
        expect(el.getAttribute("type")).toBe("application/json");
    });

    it('add 2 records in non-empty body', function() {
        doc.body.appendChild(doc.createElement("p"));

        mdtrx.set("exciting", { "@context": [], name: "Hank" })

        expect(doc.body.firstElementChild).not.toBeNull();
        mdt.serializeMetadataTransferFactory(doc, mdtrx)();

        let el = doc.body.firstElementChild;
        expect(el.tagName).toBe("SCRIPT");
        expect(el.getAttribute("id")).toBe("boring");
        expect(el.getAttribute("type")).toBe("application/json");

        let els = doc.body.getElementsByTagName("SCRIPT");
        expect(els.length).toBe(2);
        expect(els[1].tagName).toBe("SCRIPT");
        expect(els[1].getAttribute("id")).toBe("exciting");
        expect(els[1].getAttribute("type")).toBe("application/ld+json");
    });

    it('resists XSS/injection attacks', function() {
        let id = 'gotcha">null</scripts>Help!<scripts id="'
        mdtrx = new MetadataTransfer();
        mdtrx.set(id, { title: "All about me!" });

        expect(doc.body.firstElementChild).toBeNull();
        mdt.serializeMetadataTransferFactory(doc, mdtrx)();
        expect(doc.body.firstElementChild).not.toBeNull();

        let el = doc.body.firstElementChild;
        let idatt = el.getAttribute("id");
        console.log("TESTING: metadata saved with id='"+idatt+"'");
        expect(idatt).not.toBe(id);
        expect(idatt.includes(">")).not.toBe(true);
        expect(idatt.includes("<")).not.toBe(true);
        expect(idatt.includes('"')).not.toBe(true);
        expect(idatt.includes("&")).toBe(true);

        
    });

});
