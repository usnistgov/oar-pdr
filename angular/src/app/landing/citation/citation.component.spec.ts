import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';

import { CitationModule } from './citation.module';
import { CitationDescriptionComponent, CitationPopupComponent } from './citation.component';

describe('CitationDescriptionComponent', () => {
    let component : CitationDescriptionComponent;
    let fixture : ComponentFixture<CitationDescriptionComponent>;

    let setupComponent = function(citetext : string) {
        component = null;
        TestBed.configureTestingModule({
            imports: [ CitationModule ],
            declarations: [  ],
            providers: [
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(CitationDescriptionComponent);
        component = fixture.componentInstance;
        component.citetext = citetext
        fixture.detectChanges();
    }

    it("layout", () => {
        setupComponent("It's all about me!");
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll(".citation");
        expect(pels.length).toEqual(1);
        expect(pels[0].textContent).toEqual("It's all about me!");

        pels = cmpel.querySelectorAll("a");
        expect(pels.length).toEqual(1);
        expect(pels[0].textContent).toContain("Recommendations");
    });
});

describe('CitationPopupComponent', () => {
    let component : CitationPopupComponent;
    let fixture : ComponentFixture<CitationPopupComponent>;

    let setupComponent = function(citetext : string) {
        component = null;
        TestBed.configureTestingModule({
            imports: [ CitationModule ],
            declarations: [ ],
            providers: [
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(CitationPopupComponent);
        component = fixture.componentInstance;
        component.citetext = citetext
        component.visible = true;
        fixture.detectChanges();
    }

    it("layout", () => {
        setupComponent("It's all about me!");
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("citation-display");
        expect(pels.length).toEqual(1);

        pels = cmpel.querySelectorAll("p-dialog");
        expect(pels.length).toEqual(1);

        pels = cmpel.querySelectorAll("button");
        expect(pels.length).toEqual(1);

        pels = cmpel.querySelectorAll(".citation");
        expect(pels.length).toEqual(1);
        expect(pels[0].textContent).toEqual("It's all about me!");

        pels = cmpel.querySelectorAll("a");
        expect(pels.length).toEqual(1);
        expect(pels[0].textContent).toContain("Recommendations");
    });
});
