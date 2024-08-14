import { ComponentFixture, TestBed, ComponentFixtureAutoDetect, waitForAsync  } from '@angular/core/testing';

import { ResourceRefsComponent } from './resourcerefs.component';
import { SectionsModule } from './sections.module';

import { AppConfig } from '../../config/config';
import { NerdmRes, NerdmComp } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';

import { config, testdata } from '../../../environments/environment';

describe('ResourceRefsComponent', () => {
    let component: ResourceRefsComponent;
    let fixture: ComponentFixture<ResourceRefsComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ SectionsModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                GoogleAnalyticsService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ResourceRefsComponent);
        component = fixture.componentInstance;
    }

    beforeEach(waitForAsync(() => {
        makeComp();
        component.inBrowser = true;
        component.record = JSON.parse(JSON.stringify(rec));
        component.ngOnChanges({});
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeTruthy();
        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#references")).toBeTruthy();

        expect(component.hasDisplayableReferences()).toBeTruthy();

        // has 2 references
        let els = cmpel.querySelectorAll("a")
        expect(els.length).toBe(2);
    });

    it('should suppress for empty list', () => {
        expect(component).toBeTruthy();
        component.record['references'] = [];
        component.ngOnChanges({});
        fixture.detectChanges();
        
        expect(component.hasDisplayableReferences()).toBeFalsy();

        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#references")).toBeTruthy();
        expect(cmpel.querySelector("h3")).toBeFalsy();
        let els = cmpel.querySelectorAll("a")
        expect(els.length).toBe(0);
    });

    it('should not render ref as a link without location', () => {
        // remove the locations from the two reference
        component.record['references'][0]['location'] = null;
        delete component.record['references'][1].location;
        component.ngOnChanges({});
        fixture.detectChanges();

        expect(component).toBeTruthy();
        let cmpel = fixture.nativeElement;
        let reflist = cmpel.querySelector("#references");
        expect(reflist).toBeTruthy();

        // has 2 references
        let els = cmpel.querySelectorAll(".ref-entry")
        expect(els.length).toBe(2);
        els = cmpel.querySelectorAll("a");
        expect(els.length).toBe(0);
    });

    it('getReferenceText()', () => {
        expect(component).toBeTruthy();
        let ref = { 'location': 'http://example.com/doc.txt' }
        expect(component.getReferenceText(ref)).toBe('http://example.com/doc.txt');
        ref['label'] = 'an explanation'
        expect(component.getReferenceText(ref)).toBe('an explanation');
        ref['citation'] = 'Me 2001, The Explanation';
        expect(component.getReferenceText(ref)).toBe('Me 2001, The Explanation');
        delete ref['location'];
        expect(component.getReferenceText(ref)).toBe('Me 2001, The Explanation');
        delete ref['label'];
        expect(component.getReferenceText(ref)).toBe('Me 2001, The Explanation');
        ref['label'] = 'drivel'
        delete ref['citation']
        expect(component.getReferenceText(ref)).toBe('drivel');
    });
});
