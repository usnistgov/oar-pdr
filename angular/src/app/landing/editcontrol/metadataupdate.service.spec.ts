import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { MetadataUpdateService } from './metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { CustomizationService, InMemCustomizationService } from './customization.service';

import { testdata } from '../../../environments/environment';

fdescribe('MetadataUpdateService', () => {

    let rec = testdata['test1'];
    let resmd : {} = null;
    let svc : MetadataUpdateService = null;

    let subscriber = {
        next: (md) => {
            resmd = md;
        }
    };

    beforeEach(() => {
        resmd = null;
        svc = new MetadataUpdateService(new UserMessageService());
        svc._setCustomizationService(new InMemCustomizationService(rec));
    });

    it('returns initial draft metadata', () => {
        var md = null;
        svc._subscribe({
            next: (res) => { md = res; },
            error: (err) => { throw err; }
        }); 

        svc.loadDraft();
        expect(md['title']).toContain("Multiple Encounter");
        expect(md['accessLevel']).toBe("public");
        expect(Object.keys(md)).not.toContain("goober");
    });

    it('updates metadata', () => {
        resmd = testdata['test1'];
        expect(resmd['title']).toContain("Multiple Encounter");
        expect(resmd['accessLevel']).toBe("public");

        var md = null;
        svc._subscribe({
            next: (res) => { md = res; },
            error: (err) => { throw err; }
        }); 
        svc.update({'goober': "gurn", 'title': "Dr."});
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");
    });

});
