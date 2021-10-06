import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FootbarComponent } from './footbar.component';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import * as footerlinks from '../../assets/site-constants/footer-links.json';

const footerLinks: any = (footerlinks as any).default;

describe('FootbarComponent', () => {
    let component : FootbarComponent;
    let fixture : ComponentFixture<FootbarComponent>;

    it('should contain expected content', async(() => {
        TestBed.configureTestingModule({
            declarations: [ FootbarComponent ],
            providers: [GoogleAnalyticsService]
        }).compileComponents();

        fixture = TestBed.createComponent(FootbarComponent);
        component = fixture.componentInstance;

        fixture.whenStable().then(() => {
            expect(component).toBeDefined();
        })
    }));
});
