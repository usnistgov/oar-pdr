import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { AboutdatasetComponent } from './aboutdataset.component';
import { AboutdatasetModule } from './aboutdataset.module';
import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { config, testdata } from '../../../environments/environment';
import { By } from "@angular/platform-browser";
import { MetricsData } from "../metrics-data";

import * as _ from 'lodash-es';

describe('AboutdatasetComponent', () => {
    let component: AboutdatasetComponent;
    let fixture: ComponentFixture<AboutdatasetComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];

    beforeEach(waitForAsync(() => {
        TestBed.configureTestingModule({
            imports: [ AboutdatasetModule ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                GoogleAnalyticsService
            ]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(AboutdatasetComponent);
        component = fixture.componentInstance;
        component.record = rec;
        component.inBrowser = true;
        component.metricsData = new MetricsData();
        component.showJsonViewer = true;
        component.theme = 'nist';
        component.ngOnChanges({});
        fixture.detectChanges();
    });

    it('should create', () => {
        component.mobileMode = false;
        expect(component).toBeTruthy();

        let cmpel = fixture.nativeElement;
        let jsonViewer = cmpel.querySelector("#json-viewer");
        expect(jsonViewer).toBeTruthy();

        //For nornal mode, there should be 4 expand buttons ("1", "2", "3", "View Full Tree")
        let jsonExpandButtons = fixture.debugElement.queryAll(By.css('li'));
        expect(jsonExpandButtons.length).toBe(4);

        //For mobile mode, there should be only 3 expand buttons ("1", "2", "Full Tree")
        component.mobileMode = true;
        fixture.detectChanges();
        jsonExpandButtons = fixture.debugElement.queryAll(By.css('li'));
        expect(jsonExpandButtons.length).toBe(3);

        let el = cmpel.querySelector("#cite");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("Cite this dataset");

        el = cmpel.querySelector("#metadata");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("Repository Metadata");

        el = cmpel.querySelector("#metrics");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("Access Metrics");

        // test record does not include isPartOf
        el = cmpel.querySelector("#about-ispartof");
        expect(el).toBeFalsy();
    });

    it('single isPartOf rendering', () => {
        let cmpel = fixture.nativeElement;
        let member = _.cloneDeep(rec);
        member['isPartOf'] = [{
            "@id": "ark:/88888/goober",
            title: "Uber Research",
            "@type": [ "nrda:Aggregation", "nrd:PublicDataResource" ]
        }];
        component.record = member;
        component.ngOnInit();
        fixture.detectChanges();

        let el = cmpel.querySelector("#about-ispartof");
        expect(el).toBeTruthy();
        expect(el.querySelector("ul")).toBeFalsy();
        expect(el.innerHTML.includes(" collection.")).toBeTruthy();
        let a = el.querySelector("a");
        expect(a).toBeTruthy();
        expect(a.href.endsWith("/ark:/88888/goober")).toBeTruthy();
    });

    it('multiple isPartOf rendering', () => {
        let cmpel = fixture.nativeElement;
        let member = _.cloneDeep(rec);
        member['isPartOf'] = [
            {
                "@id": "ark:/88888/goober",
                title: "Uber Research",
                "@type": [ "nrda:ScienceTheme", "nrd:PublicDataResource" ]
            },
            {
                "@id": "ark:/88888/gomer",
                title: "Sleepy Research",
                "@type": [ "nrda:Aggregation", "nrd:PublicDataResource" ]
            }
        ];
        component.record = member;
        component.ngOnInit();
        fixture.detectChanges();

        let el = cmpel.querySelector("#about-ispartof");
        expect(el).toBeTruthy();
        expect(el.querySelector("ul")).toBeTruthy();
        expect(el.innerHTML.includes("This dataset is part of")).toBeTruthy();
        let li = el.querySelectorAll("ul li");
        expect(li.length).toEqual(2);
        expect(li[0].innerHTML.includes(" Collection ")).toBeTruthy();
        let html = li[1].innerHTML
        expect(li[1].innerHTML.includes("Science Theme")).toBeFalsy();
        expect(li[1].innerHTML.endsWith("collection ")).toBeFalsy();
        expect(li[0].querySelector("a").href.endsWith("/ark:/88888/goober")).toBeTruthy();
        expect(li[1].querySelector("a").href.endsWith("/ark:/88888/gomer")).toBeTruthy();
    });

    it('getDownloadURL()', () => {
        let url = component.getDownloadURL().substring(component.getDownloadURL().split("/", 3).join("/").length);
        expect(url).toEqual("/rmm/records/?@id=ark:/88434/mds0000fbk");
    });
});
