import { ElementRef } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { TransferState } from '@angular/platform-browser';
import { Title }    from '@angular/platform-browser';
import { ActivatedRoute, Router, Routes } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { LandingPageModule } from './landingPage.module';
import { LandingPageComponent } from './landingPage.component';
import { AngularEnvironmentConfigService } from '../config/config.service';
import { AppConfig } from '../config/config'
import { MetadataTransfer, NerdmRes } from '../nerdm/nerdm'
import { MetadataService, TransferMetadataService } from '../nerdm/nerdm.service'
import { CommonVarService } from '../shared/common-var';
import { CartService } from "../datacart/cart.service";
import { DownloadService } from "../shared/download-service/download-service.service";
import { TestDataService } from '../shared/testdata-service/testDataService';
import * as mock from '../testing/mock.services';
import {RouterTestingModule} from "@angular/router/testing";
import { testdata } from '../../environments/environment';

describe('LandingPageComponent', () => {
    let component : LandingPageComponent;
    let fixture : ComponentFixture<LandingPageComponent>;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();
    let nrd : NerdmRes;
    let mdt : MetadataTransfer;
    let mds : MetadataService;
    let route : ActivatedRoute;
    let router : Router;
    let title : mock.MockTitle;

    let routes : Routes = [
        { path: 'od/id/:id', component: LandingPageComponent },
        { path: 'od/id/ark:/88434/:id', component: LandingPageComponent }
    ];

    beforeEach(() => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";

        nrd = testdata['test1'];
        /*
        nrd = {
            "@type": [ "nrd:SRD", "nrdp:DataPublication", "nrdp:DataPublicResource" ],
            "@id": "goober",
            title: "All About Me!"
        }
        */
        mdt = new MetadataTransfer();
        mdt.set("NERDm Resource:goober", nrd)
        mds = new TransferMetadataService(mdt);

        let r : unknown = new mock.MockActivatedRoute("/id/goober", {id: "goober"});
        route = r as ActivatedRoute;
    });

    let setupComponent = function() {
        TestBed.configureTestingModule({
            imports: [ HttpClientModule, BrowserAnimationsModule, LandingPageModule,
                       RouterTestingModule.withRoutes(routes) ],
            providers: [
                { provide: ActivatedRoute,  useValue: route },
                { provide: ElementRef,      useValue: null },
                { provide: AppConfig,       useValue: cfg },
                { provide: MetadataService, useValue: mds },
                CommonVarService, CartService, DownloadService, TestDataService
            ]
        }).compileComponents();

        router = TestBed.get(Router);
        fixture = TestBed.createComponent(LandingPageComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    }

    it("should set title bar", function() {
        setupComponent();
        expect(component.getDocumentTitle()).toBe("PDR: "+nrd.title);
    });

    it("includes landing display", function() {
        setupComponent();
        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("h2"); 
        expect(el.textContent).toBe(nrd.title);
    });

});
