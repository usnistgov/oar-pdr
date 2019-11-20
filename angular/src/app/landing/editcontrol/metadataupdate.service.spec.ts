import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule, DatePipe } from '@angular/common';
import { of, throwError } from 'rxjs';

import { MetadataUpdateService } from './metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { CustomizationService, InMemCustomizationService } from './customization.service';
import { NerdmRes } from '../../nerdm/nerdm';

import { testdata } from '../../../environments/environment';

describe('MetadataUpdateService', () => {

    let rec : NerdmRes = testdata['test1'];
    let resmd : NerdmRes = null;
    let svc : MetadataUpdateService = null;

    let subscriber = {
        next: (md) => {
            resmd = md;
        }
    };

    beforeEach(async(() => {
        resmd = null;
        TestBed.configureTestingModule({
            imports: [ CommonModule ],
            providers: [ DatePipe ]
        });
        let dp : DatePipe = TestBed.get(DatePipe);
        svc = new MetadataUpdateService(new UserMessageService(), dp);
        svc._setCustomizationService(new InMemCustomizationService(rec));
    }));

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
        let upd : boolean = null;
        resmd = testdata['test1'];
        expect(resmd['title']).toContain("Multiple Encounter");
        expect(resmd['accessLevel']).toBe("public");

        expect(svc.fieldUpdated('gurn')).toBeFalsy();
        svc.updated.subscribe((res) => { upd = res; });
        expect(upd).toBeNull();
        expect(svc.lastUpdate).toBe("");

        var md = null;
        svc._setOriginalMetadata(resmd);
        svc._subscribe({
            next: (res) => { md = res; },
            error: (err) => { throw err; }
        }); 
        svc.update('gurn', {'goober': "gurn", 'title': "Dr."});
        expect(md['title']).toBe("Dr.");
        expect(md['accessLevel']).toBe("public");
        expect(md['goober']).toBe("gurn");

        expect(svc.fieldUpdated('gurn')).toBeTruthy();
        expect(upd).toBeTruthy();
        expect(svc.lastUpdate).not.toBe("");
    });

    it('undo()', () => {
        expect(svc.fieldUpdated('gurn')).toBeFalsy();

        var md = null;
        svc._setOriginalMetadata(rec);
        svc._subscribe({
            next: (res) => { md = res; },
            error: (err) => { throw err; }
        }); 
        svc.update('gurn', {'goober': "gurn", 'title': "Dr."});
        expect(svc.fieldUpdated('gurn')).toBeTruthy();
        expect(md['title']).toBe("Dr.");
        expect(md['goober']).toBe("gurn");
        expect(md['description'].length).toEqual(1);
        svc.update("description", { description: rec['description'].concat(['Hah!']) });
        expect(md['description'].length).toEqual(2);
        expect(md['description'][1]).toEqual("Hah!");

        svc.undo('gurn');
        expect(svc.fieldUpdated('gurn')).toBeFalsy();
        expect(md['goober']).toBe(null);
        expect(md['title']).toContain("Multiple Encounter");
        expect(md['description'].length).toEqual(2);
        expect(md['description'][1]).toEqual("Hah!");
        
    });

    it('final undo()', () => {
        expect(svc.fieldUpdated('gurn')).toBeFalsy();

        var md = null;
        svc._setOriginalMetadata(rec);
        svc._subscribe({
            next: (res) => { md = res; },
            error: (err) => { throw err; }
        }); 
        svc.update('gurn', {'goober': "gurn", 'title': "Dr."});
        expect(svc.fieldUpdated('gurn')).toBeTruthy();
        expect(md['title']).toBe("Dr.");

        svc.undo('gurn');
        expect(svc.fieldUpdated('gurn')).toBeFalsy();
        expect(md['goober']).toBe(undefined);
        expect(md['title']).toContain("Multiple Encounter");
        
    });

});
