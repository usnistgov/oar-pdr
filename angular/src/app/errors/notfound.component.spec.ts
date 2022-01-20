import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';

import { NotFoundComponent } from './notfound.component';
import * as mock from '../testing/mock.services';

describe('NotFoundComponent', () => {
    let component : NotFoundComponent;
    let fixture : ComponentFixture<NotFoundComponent>;
    let route : ActivatedRoute;

    beforeEach(() => {
    });

    let setupComponent = function(id) {
        let path = "/not-found";
        let params = {};
        if (id) {
            path = path + "/" + id;
            params['id'] = id;
        }
        let r : unknown = new mock.MockActivatedRoute(path, params);
        route = r as ActivatedRoute;

        component = null;
        TestBed.configureTestingModule({
            imports: [ CommonModule ],
            declarations: [ NotFoundComponent ],
            providers: [
                { provide: ActivatedRoute,  useValue: route },
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(NotFoundComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    }

    it('should contain requested ID', () => {
        setupComponent("goober");
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(1);
        expect(pels[0].textContent.includes("ID not found:")).toBe(true)
        expect(pels[0].textContent.includes("goober")).toBe(true)
    });

    it('should contain expected content, but no ID', () => {
        setupComponent(null);
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(1);
        expect(pels[0].textContent.includes("URL not found")).toBe(true)
        expect(pels[0].textContent.includes("found:")).toBe(false)
    });

    it('should prevent injection attacks', () => {
        setupComponent('<a href="badurl">ID</a>');
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(1);
        expect(pels[0].textContent.includes("ID not found")).toBe(true)
        pels = cmpel.querySelectorAll("a");
        expect(pels.length).not.toBeGreaterThan(0);

    });
});
