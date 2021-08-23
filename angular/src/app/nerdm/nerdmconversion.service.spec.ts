import * as convert from './nerdmconversion.service';
import { config, testdata } from '../../environments/environment';
import { NerdmRes } from './nerdm';
import { AppConfig } from '../config/config';
import { async } from '@angular/core/testing';

describe('convert functions', function() {

    it('nerdm2schemaorg', () => {
        let so = convert.nerdm2schemaorg(testdata['test1']);
        expect(Object.keys(so).length).toBeGreaterThan(5);
        expect(so['@context']).toEqual("https://schema.org");
        expect(so['@type']).toEqual("Dataset");
        expect(so.about).toEqual(testdata['test1']['@id']);
        expect(so.name).toEqual(testdata['test1']['title']);
        expect(so.publisher).toBeTruthy();
        expect(so.publisher.name).toBe("National Institute of Standards and Technology");
        expect(so.publisher['@type']).toEqual("Organization");
        expect(so.maintainer).toBeTruthy();
        expect(so.maintainer['@type']).toEqual("Person");
        expect(so.maintainer['name']).toEqual("Patricia Flanagan");
        expect(so.maintainer['email']).toEqual("patricia.flanagan@nist.gov");
        expect(so.citation).toBeTruthy();
        expect(so.creator).toBeTruthy();
        expect(so.creator.length).toEqual(1);
        expect(so.creator[0]).toEqual(so.maintainer);
        expect(so.mainEntityOfPage).toEqual(testdata['test1']['landingPage']);
        expect(so.url).toEqual("https://data.nist.gov/od/id/26DEA39AD677678AE0531A570681F32C1449");
    });
});

describe('convert functions', function() {

    let svc: convert.NerdmConversionService = null;

    beforeEach(() => {
        let cfg = JSON.parse(JSON.stringify(config));
        cfg['embedMetadata'] = [convert.SchemaLabel.SCHEMA_ORG];
        let appcfg = new AppConfig(cfg);
        svc = new convert.NerdmConversionService(appcfg);
    });

    it('constructor', () => {
        expect(svc.supportedFormats()).toEqual([convert.SchemaLabel.SCHEMA_ORG]);
        expect(svc.supportsFormat(convert.SchemaLabel.SCHEMA_ORG)).toBeTruthy();
        expect(svc.supportsFormat("scare")).toBeFalsy();
        expect(svc.formatsToEmbed()).toEqual([convert.SchemaLabel.SCHEMA_ORG]);

        svc = new convert.NerdmConversionService(new AppConfig(config));  // embedMetadata not included
        expect(svc.formatsToEmbed()).toEqual([]);
    });

    it('supportConversion', () => {
        svc.supportConversion("scare", (md: NerdmRes): string => { return "boo!"; }, "text/plain");
        expect(svc.supportsFormat(convert.SchemaLabel.SCHEMA_ORG)).toBeTruthy();
        expect(svc.supportsFormat("scare")).toBeTruthy();
        expect(svc.supportsFormat("goob")).toBeFalsy();
    });

    it('convertTo()', () => {
        let so = svc.convertTo(testdata['test1'], convert.SchemaLabel.SCHEMA_ORG);
        expect(so.contentType).toEqual("application/ld+json");
        expect(so.label).toEqual(convert.SchemaLabel.SCHEMA_ORG);

        expect(Object.keys(so.md).length).toBeGreaterThan(5);
        expect(so.md['@context']).toEqual("https://schema.org");
        expect(so.md['@type']).toEqual("Dataset");
        expect(so.md['about']).toEqual(testdata['test1']['@id']);
        expect(so.md['name']).toEqual(testdata['test1']['title']);
        expect(so.md['publisher']).toBeTruthy();
        expect(so.md['citation']).toBeTruthy();
        expect(so.md['mainEntityOfPage']).toEqual(testdata['test1']['landingPage']);
        expect(so.md['url']).toEqual("https://data.nist.gov/od/id/26DEA39AD677678AE0531A570681F32C1449");

        expect(svc.convertTo(testdata['test1'], "scare")).toBeNull();

        svc.supportConversion("scare", (md: NerdmRes): string => { return "boo!"; }, "text/plain");
        so = svc.convertTo(testdata['test1'], "scare");
        expect(so.contentType).toEqual("text/plain");
        expect(so.label).toEqual("scare");
        expect(so.md).toEqual("boo!");
    });

    it('convertToEmbedFormats()', async(() => {
        svc.convertToEmbedFormats(testdata['test1']).subscribe({
            next(so) {
                expect(so.contentType).toEqual("application/ld+json");
                expect(so.label).toEqual(convert.SchemaLabel.SCHEMA_ORG);
                expect(Object.keys(so.md).length).toBeGreaterThan(5);
                expect(so.md['@context']).toEqual("https://schema.org");
                expect(so.md['@type']).toEqual("Dataset");
                expect(so.md['about']).toEqual(testdata['test1']['@id']);
            },
            error(e) { fail("schema.org conversion failed: "+e); }
        });

        svc.supportConversion("scare", (md: NerdmRes): string => { return "boo!"; }, "text/plain");
        svc.convertToEmbedFormats(testdata['test1']).subscribe({
            next(so) {
                if (typeof so.md === 'string') {
                    expect(so.contentType).toEqual("text/plain");
                    expect(so.label).toEqual("scare");
                    expect(so.md).toEqual("boo!");
                }
                else {
                    expect(so.contentType).toEqual("application/ld+json");
                    expect(so.label).toEqual(convert.SchemaLabel.SCHEMA_ORG);
                    expect(Object.keys(so.md).length).toBeGreaterThan(5);
                    expect(so.md['@context']).toEqual("https://schema.org");
                    expect(so.md['@type']).toEqual("Dataset");
                    expect(so.md['about']).toEqual(testdata['test1']['@id']);
                }
            },
            error(e) { fail("conversion failed: "+e); }
        });
    }));
});
