import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SearchresultComponent } from './searchresult.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations'; 

describe('SearchresultComponent', () => {
    let component: SearchresultComponent;
    let fixture: ComponentFixture<SearchresultComponent>;

    beforeEach(async () => {
        await TestBed.configureTestingModule({
        declarations: [ SearchresultComponent ],
        imports: [BrowserAnimationsModule]
        })
        .compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SearchresultComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });
});
