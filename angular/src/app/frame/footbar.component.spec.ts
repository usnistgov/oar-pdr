import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FootbarComponent } from './footbar.component';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';


describe('FootbarComponent', () => {
    let component : FootbarComponent;
    let fixture : ComponentFixture<FootbarComponent>;

    it('should contain expected content', () => {
        TestBed.configureTestingModule({
            declarations: [ FootbarComponent ],
            providers: [GoogleAnalyticsService]
        }).compileComponents();

        fixture = TestBed.createComponent(FootbarComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();

        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let aels = cmpel.querySelectorAll("a");
        expect(aels.length).toBeGreaterThan(3);
        let links = [];
        for (let i = 0; i < aels.length; i++)
            links.push(aels[i].getAttribute("href"));
        expect(links.includes("https://twitter.com/USNISTGOV")).toBe(true);
        expect(links.includes("https://www.facebook.com/USNISTGOV")).toBe(true);
        expect(links.includes("https://www.youtube.com/user/USNISTGOV")).toBe(true);
        expect(links.includes("https://nist.gov/")).toBe(true);
    });
});
