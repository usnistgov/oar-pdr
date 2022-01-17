import { async, ComponentFixture, TestBed, ComponentFixtureAutoDetect } from '@angular/core/testing';

import { AppConfig } from '../../config/config';
import { NerdmRes } from '../../nerdm/nerdm';
import { VersionComponent, compare_versions, normalize_date, compare_dates, compare_histories }
    from './version.component';
import { VersionModule } from './version.module';

import { config, testdata } from '../../../environments/environment';
import { LandingConstants } from '../constants';

describe('VersionComponent', () => {
    let component : VersionComponent;
    let fixture : ComponentFixture<VersionComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];
    let EDIT_MODES = LandingConstants.editModes;

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ VersionModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(VersionComponent);
        component = fixture.componentInstance;
        component.record = JSON.parse(JSON.stringify(rec));
        // fixture.detectChanges();
    }

    beforeEach(async(() => {
        makeComp();
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();
        let cmpel = fixture.nativeElement;
        let spans = cmpel.querySelectorAll("span"); 
        expect(spans[0].textContent).toContain("Version:");
        expect(spans[0].textContent).toContain("1.0");
        expect(spans[2].textContent).toContain("First Released:");
        expect(spans[2].textContent).toContain("2019-03-27");
        expect(spans[3].textContent).toContain("Revised:");
        expect(spans[3].textContent).toContain("2019-03-28");
    });

    it('test renderRelAsLink()', () => {
        let rel = JSON.parse(JSON.stringify(rec.releaseHistory.hasRelease[0]));
        let html = component.renderRelAsLink(rel, "one version");
        expect(html).toContain('<a href="https://data.nist.gov/od/id/mds0000fbk/pdr:v/1.0.0">one version</a>');

        rel.location = undefined;
        html = component.renderRelAsLink(rel, "one version");
        expect(html).toContain('<a href="https://data.nist.gov/od/id/ark:/88434/mds0000fbk/pdr:v/1.0.0">one version</a>');

        rel['@id'] = "doi:10.88434/mine";
        html = component.renderRelAsLink(rel, "one version");
        expect(html).toContain('<a href="https://doi.org/10.88434/mine">one version</a>');

        rel['@id'] = "https://dx.doi.org/10.88434/mine";
        html = component.renderRelAsLink(rel, "one version");
        expect(html).toContain('<a href="https://dx.doi.org/10.88434/mine">one version</a>');
    });

    it('test renderRelVer()', () => {
        let rel = JSON.parse(JSON.stringify(rec.releaseHistory.hasRelease[0]));
        let html = component.renderRelVer(rel, "1.2.1");
        expect(html).toContain('<a href="https://data.nist.gov/od/id/mds0000fbk/pdr:v/1.0.0">v1.0.0</a>');

        html = component.renderRelVer(rel, "1.0.0");
        expect(html).toBe('v1.0.0');
    });

    it('test renderRelId()', () => {
        let rel = JSON.parse(JSON.stringify(rec.releaseHistory.hasRelease[0]));
        let html = component.renderRelId(rel, "1.2.1");
        expect(html).toContain('<a href="https://data.nist.gov/od/id/mds0000fbk/pdr:v/1.0.0">ark:/88434/mds0000fbk/pdr:v/1.0.0</a>');

        component.editMode = EDIT_MODES.editMode;
        html = component.renderRelId(rel, "1.2.1");
        expect(html).toBe('ark:/88434/mds0000fbk/pdr:v/1.0.0');
        component.editMode = EDIT_MODES.VIEWONLY_MODE;
        
        html = component.renderRelId(rel, "1.0.0");
        expect(html).toBe('this version');

        rel['@id'] = undefined; 
        html = component.renderRelId(rel, "1.1.1");
        expect(html).toBe('<a href="https://data.nist.gov/od/id/mds0000fbk/pdr:v/1.0.0">View...</a>');

        component.editMode = EDIT_MODES.editMode;
        html = component.renderRelId(rel, "1.1.1");
        expect(html).toBe('View...');
    });

    it('test newer()', () => {
        expect(component.newer).toBeNull();
        let cmpel = fixture.nativeElement;
        let ps = cmpel.querySelectorAll("p"); 
        expect(ps.length).toBe(0);

        component.record['version'] = "1.0.0";
        component.assessNewer();
        expect(component.newer).not.toBeNull();
        expect(component.newer['version']).toBe("1.1.2");

        fixture.detectChanges();
        cmpel = fixture.nativeElement;
        ps = cmpel.querySelectorAll("p"); 
        expect(ps.length).toBe(1);
        expect(ps[0].textContent).toContain("more recent release");
        expect(ps[0].textContent).toContain("1.1.2");
    });

    it('test expandHistory()', () => {
        expect(component).toBeDefined();
        expect(component.visibleHistory).toBeFalsy();
        let cmpel = fixture.nativeElement;
        let divs = cmpel.querySelectorAll("div"); 
        expect(divs.length).toBe(4);
        expect(divs[1].style.display).toBe("none");

        component.expandHistory();
        expect(component.visibleHistory).toBeTruthy();

        /*
         * can't figure out how to trigger rerendering within unit test
         *
        fixture.detectChanges();
        component.ngOnChanges();
        divs = cmpel.querySelectorAll("div"); 
        expect(divs.length).toBe(4);
        expect(divs[1].style.display).not.toBe("none");
         */
    });

});

describe("version compare functions", () => {

    it('compare_version', () => {
        expect(compare_versions("8", "15")).toBeLessThan(0);
        expect(compare_versions("28", "5")).toBeGreaterThan(0);
        expect(compare_versions("5", "5")).toBe(0);

        expect(compare_versions("8.1.0", "15.2.56")).toBeLessThan(0);
        expect(compare_versions("28.0", "5.8.4")).toBeGreaterThan(0);
        expect(compare_versions("5", "5.0")).toBeLessThan(0);

        expect(compare_versions("8.1", "8.1.5")).toBeLessThan(0); 
        expect(compare_versions("5.8.1", "5.0.4")).toBeGreaterThan(0);
        expect(compare_versions("5", "5.1")).toBeLessThan(0);

        expect(compare_versions("8.1.3", "8.1.5")).toBeLessThan(0);
        expect(compare_versions("5.8.5", "5.8.4")).toBeGreaterThan(0);
        expect(compare_versions("5.3.2.1", "5.1")).toBeGreaterThan(0);

        expect(compare_versions("5.3.2rc8", "5.3.2rc8")).toBe(0);
        expect(compare_versions("5.3.2rc12", "5.3.2rc8")).toBeGreaterThan(0);
        expect(compare_versions("5.3.2", "5.3.2rc8")).toBeLessThan(0);
        expect(compare_versions("5.3.2rc12", "5.3.2")).toBeGreaterThan(0);
    });

    it("normalize_date", () => {
        expect(normalize_date("2017")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01T00:00")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00:00")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00:00.093")).toBe("2017-01-01T00:00:00.093");

        expect(normalize_date("2017Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01T00:00Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00:00Z-0530")).toBe("2017-01-01T00:00:00");
        expect(normalize_date("2017-01-01 00:00:00.093Z-0530")).toBe("2017-01-01T00:00:00.093");
    });

    it("compare_dates", () => {
        expect(compare_dates("2017", "1995")).toBeGreaterThan(0);
        expect(compare_dates("2009", "2020")).toBeLessThan(0);
        expect(compare_dates("2009", "2009")).toBe(0);
        
        expect(compare_dates("2017-01", "1995-01")).toBeGreaterThan(0);
        expect(compare_dates("2009-10", "2020-03")).toBeLessThan(0);
        expect(compare_dates("2017-01", "2017-10")).toBeLessThan(0);
        expect(compare_dates("2017-12", "2017-10")).toBeGreaterThan(0);
        expect(compare_dates("2017-12", "2017-12")).toBe(0);
        
        expect(compare_dates("2017-01-09", "1995-01-18")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09", "2020-03-18")).toBeLessThan(0);
        expect(compare_dates("2017-01-09", "2017-10-09")).toBeLessThan(0);
        expect(compare_dates("2017-12-10", "2017-10-10")).toBeGreaterThan(0);
        expect(compare_dates("2017-12-10", "2017-12-10")).toBe(0);
        expect(compare_dates("2017-01-29", "2017-01-18")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09", "2009-10-18")).toBeLessThan(0);
        
        expect(compare_dates("2017-01-09T05:01", "1995-01-18T10:01")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09T05:01", "2020-03-18T10:01")).toBeLessThan(0);
        expect(compare_dates("2017-01-09T05:01", "2017-10-09T10:01")).toBeLessThan(0);
        expect(compare_dates("2017-12-10T05:01", "2017-10-10T10:01")).toBeGreaterThan(0);
        expect(compare_dates("2017-12-10T10:01", "2017-12-10T10:01")).toBe(0);
        expect(compare_dates("2017-12-10 10:01", "2017-12-10 10:01")).toBe(0);
        expect(compare_dates("2017-12-10 10:01", "2017-12-10T10:01")).toBe(0);
        expect(compare_dates("2017-01-29T05:01", "2017-01-18 10:01")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09 05:01", "2009-10-18 10:01")).toBeLessThan(0);
        expect(compare_dates("2017-10-09T10:01", "2017-10-09T05:01")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09 05:36", "2009-10-09 05:45")).toBeLessThan(0);
        
        expect(compare_dates("2017-01-09T05:01:30", "1995-01-18T10:01:30")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09T10:01:45", "2020-03-18T10:01:30")).toBeLessThan(0);
        expect(compare_dates("2017-01-09T10:01:30", "2017-10-09T10:01:51")).toBeLessThan(0);
        expect(compare_dates("2017-12-10T05:01:30", "2017-10-10T10:01:30")).toBeGreaterThan(0);
        expect(compare_dates("2017-12-10T10:01:30", "2017-12-10T10:01:30")).toBe(0);
        expect(compare_dates("2017-12-10T10:01:30", "2017-12-10 10:01:30")).toBe(0);
        expect(compare_dates("2017-12-10 10:01:30", "2017-12-10T10:01:30")).toBe(0);
        expect(compare_dates("2017-12-10 10:01:30", "2017-12-10 10:01:30")).toBe(0);
        expect(compare_dates("2017-01-29T05:01:30", "2017-01-18T10:01:30")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09T05:01:30", "2009-10-18T10:01:30")).toBeLessThan(0);
        expect(compare_dates("2017-10-09 10:01:30", "2017-10-09T05:01:30")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09T05:36:30", "2009-10-09T05:45:30")).toBeLessThan(0);
        expect(compare_dates("2017-10-09 10:01:30", "2017-10-09 10:01:18")).toBeGreaterThan(0);
        expect(compare_dates("2009-10-09 05:36:30", "2009-10-09 05:36:31")).toBeLessThan(0);

        //expect(Date.parse("2017-12-10")).toBe(Date.parse("2017-12-10 00:00:00"));
        expect(compare_dates("2017", "2017-01-01 00:00:00")).toBe(0);
        expect(compare_dates("2017-12", "2017-12-01 00:00:00")).toBe(0);
        expect(compare_dates("2017-12-10", "2017-12-10 00:00:00")).toBe(0);
        expect(compare_dates("2017-12-10 00:00", "2017-12-10 00:00:00")).toBe(0);
        expect(compare_dates("2017-12-10T00:00", "2017-12-10 00:00:00")).toBe(0);
        expect(compare_dates("2017-12-10 00:00", "2017-12-10 00:00:00")).toBe(0);

        expect(compare_dates("2017", "2018-01-01 00:00:00")).toBeLessThan(0);
        expect(compare_dates("2017-11", "2017-11-02 00:00:00")).toBeLessThan(0);
        expect(compare_dates("2017-11-10", "2017-11-10 00:00:01")).toBeLessThan(0);
        expect(compare_dates("2017-11-10 00:00", "2017-11-10 00:00:01")).toBeLessThan(0);
        expect(compare_dates("2017-11-10T00:00", "2017-11-10 00:00:01")).toBeLessThan(0);
        expect(compare_dates("2017-11-10 00:00", "2017-11-10 00:00:01")).toBeLessThan(0);

        // Zone strings are ignored
        expect(compare_dates("2017Z+05", "1995")).toBeGreaterThan(0);
        expect(compare_dates("2017-12Z-10", "2017-12Z-05")).toBe(0);
        expect(compare_dates("2009-10-09", "2009-10-18Z-0130")).toBeLessThan(0);
        expect(compare_dates("2009-10-09T05:36Z", "2009-10-09T05:45")).toBeLessThan(0);
        expect(compare_dates("2009-10-09T05:36:30", "2009-10-09T05:36:31Z10")).toBeLessThan(0);
    });

    it("compare_histories", () => {
        let ha = {
            "goob": "gurn",
            "version": "2.1.4",
            "issued": "2018-05-24"
        };
        let hb = {
            "goob": "gurn",
            "version": "2.1.4",
            "issued": "2018-05-24"
        };
        expect(compare_histories(ha, hb)).toBe(0);
        expect(compare_histories(hb, ha)).toBe(0);

        ha.version = "2.0.8";
        expect(compare_histories(ha, hb)).toBeLessThan(0);
        expect(compare_histories(hb, ha)).toBeGreaterThan(0);

        ha.issued = "2020-01-15";
        expect(compare_histories(hb, ha)).toBeLessThan(0);
        expect(compare_histories(ha, hb)).toBeGreaterThan(0);
    });
});

