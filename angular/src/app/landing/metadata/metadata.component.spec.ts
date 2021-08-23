import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { MetadataComponent } from './metadata.component';
import { MetadataModule } from './metadata.module';
import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { config, testdata } from '../../../environments/environment';

describe('MetadataComponent', () => {
    let component: MetadataComponent;
    let fixture: ComponentFixture<MetadataComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec : NerdmRes = testdata['test1'];

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            imports: [ MetadataModule ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                GoogleAnalyticsService
            ]
        }).compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(MetadataComponent);
        component = fixture.componentInstance;
        component.record = rec;
        component.inBrowser = true;
        component.ngOnChanges({});
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();

        let cmpel = fixture.nativeElement;
        expect(cmpel.querySelector("#metadata-nerdm")).toBeTruthy();

        let el = cmpel.querySelector("p");
        expect(el).toBeTruthy();
        el = el.querySelector("a");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("NERDm documentation");

        expect(component.record).toBeTruthy();
        el = cmpel.querySelector("legend");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("NERDm");
    });

    it('getDownloadURL()', () => {
        expect(component.getDownloadURL()).toEqual("https://data.nist.gov/rmm/records/?@id=ark:/88434/mds0000fbk");
    });
});
