import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { TransferState } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { Component } from '@angular/core';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { HeadbarComponent } from './headbar.component';
import { AngularEnvironmentConfigService } from '../config/config.service';
import { AppConfig } from '../config/config'
import { CartService } from '../datacart/cart.service';
import { ToastrModule } from 'ngx-toastr';
import { NotificationService } from '../shared/notification-service/notification.service';
import { EditStatusService } from '../landing/editcontrol/editstatus.service';

@Component({ template: '' })
class DummyComponent {}

describe('HeadbarComponent', () => {
    let component : HeadbarComponent;
    let fixture : ComponentFixture<HeadbarComponent>;
    let cfg : AppConfig;
    let cart : CartService;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();

    it('should display configured information', () => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = "Unit Testing";
        cfg.appVersion = "2.test";
        
        TestBed.configureTestingModule({
            imports: [
                RouterTestingModule.withRoutes([
                    { path: 'datacart', component: DummyComponent }
                ]),
                HttpClientTestingModule,
                ToastrModule.forRoot()
            ],
            declarations: [ HeadbarComponent, DummyComponent ],
            providers: [
                { provide: AppConfig, useValue: cfg  },
                CartService,
                NotificationService,
                EditStatusService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(HeadbarComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();

        expect(component).toBeDefined();
        expect(component.searchLink).toBe("https://goob.nist.gov/search");
        expect(component.status).toBe("Unit Testing");
        expect(component.appVersion).toBe("2.test");

        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("#appVersion"); 
        expect(el.textContent.trim()).toBe(component.appVersion);
        el = cmpel.querySelector("#appStatus");
        expect(el.textContent.trim()).toBe(component.status);

        let aels = cmpel.querySelectorAll(".header-links a")
        expect(aels.length).toBeGreaterThan(0);
        // expect(aels[0].getAttribute('href')).toBe("/pdr/about");
        // expect(aels[1].getAttribute('href')).toBe("https://goob.nist.gov/search");
    });

    it('badges are optional', () => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = undefined;
        cfg.appVersion = undefined;
        
        TestBed.configureTestingModule({
            imports: [
                RouterTestingModule.withRoutes([
                    { path: 'datacart', component: DummyComponent }
                ]),
                HttpClientTestingModule,
                ToastrModule.forRoot()
            ],
            declarations: [ HeadbarComponent, DummyComponent ],
            providers: [
                { provide: AppConfig, useValue: cfg  },
                CartService,
                NotificationService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(HeadbarComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();

        expect(component).toBeDefined();
        expect(component.appVersion).toBe('');
        expect(component.status).toBe('');

        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("#appVersion"); 
        expect(el).toBeNull();
        el = cmpel.querySelector("#appStatus");
        expect(el).toBeNull();
    });

    it('displays active cart size', () => {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        cfg.status = undefined;
        cfg.appVersion = undefined;
        
        TestBed.configureTestingModule({
            imports: [
                RouterTestingModule.withRoutes([
                    { path: 'datacart', component: DummyComponent }
                ]),
                HttpClientTestingModule,
                ToastrModule.forRoot()
            ],
            declarations: [ HeadbarComponent, DummyComponent ],
            providers: [
                { provide: AppConfig, useValue: cfg  },
                CartService,
                NotificationService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(HeadbarComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();

        expect(component).toBeDefined();
        expect(component.cartLength).toBe(0);

    });

    afterEach(() => {
    });
});
