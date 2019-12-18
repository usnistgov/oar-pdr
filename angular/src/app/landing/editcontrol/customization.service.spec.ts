import { of, throwError } from 'rxjs';

import { CustomizationService, InMemCustomizationService } from './customization.service';

import { testdata } from '../../../environments/environment';

describe('InMemCustomizationService', () => {

    let rec = testdata['test1'];
    let svc : CustomizationService = null;

    beforeEach(() => {
        svc = new InMemCustomizationService(rec);
    });

    it('returns initial draft metadata', () => {
        let md = null;
        svc.getDraftMetadata().subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toContain("Multiple Encounter");
        expect(md['accessLevel']).toBe("public");
        expect(Object.keys(md)).not.toContain("goober");
    });

    it('updates metadata', () => {
        let md = null;
        svc.updateMetadata({'goober': "gurn", 'title': "Dr."}).subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");
    });

    it('discards updated metadata', () => {
        let md = null;
        svc.updateMetadata({'goober': "gurn", 'title': "Dr."}).subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");

        svc.discardDraft().subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toContain("Multiple Encounter");
        expect(md['accessLevel']).toBe("public");
        expect(Object.keys(md)).not.toContain("goober");
    });

    it('saves metadata', () => {
        let md = null;
        svc.updateMetadata({'goober': "gurn", 'title': "Dr."}).subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");

        svc.saveDraft().subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");

        svc.updateMetadata({'accessLevel': "private"}).subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("private");
        expect(md['goober']).toBe("gurn");

        svc.discardDraft().subscribe(
            (res) => { md = res; },
            (err) => { throw err; }
        );
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");
    });
});
