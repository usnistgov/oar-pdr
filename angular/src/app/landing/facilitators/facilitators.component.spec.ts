import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NerdmRes, NerdmComp } from '../../nerdm/nerdm';
import { FacilitatorsComponent } from './facilitators.component';
import { config, testdata } from '../../../environments/environment';

describe('FacilitatorsComponent', () => {
    let component: FacilitatorsComponent;
    let fixture: ComponentFixture<FacilitatorsComponent>;
    let rec : NerdmRes = testdata['test1'];

    beforeEach(async () => {
        await TestBed.configureTestingModule({
        declarations: [ FacilitatorsComponent ]
        })
        .compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(FacilitatorsComponent);
        component = fixture.componentInstance;
        component.inBrowser = true;
        component.record = JSON.parse(JSON.stringify(rec));
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
