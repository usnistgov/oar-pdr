import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FootbarComponent } from './footbar.component';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import * as footerlinks from '../../assets/site-constants/footer-links.json';

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
        component.footerLinks = (footerlinks as any).default;

        expect(component).toBeDefined();
    });
});
