import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { FootbarComponent } from './footbar.component';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';

describe('FootbarComponent', () => {
    let component : FootbarComponent;
    let fixture : ComponentFixture<FootbarComponent>;

    it('should contain expected content', waitForAsync(() => {
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
