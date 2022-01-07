import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';

import { InternalErrorComponent } from './internalerror.component';
import * as mock from '../testing/mock.services';

describe('InternalErrorComponent', () => {
    let component : InternalErrorComponent;
    let fixture : ComponentFixture<InternalErrorComponent>;
    let route : ActivatedRoute;

    let setupComponent = function(id) {
        let path = "/int-error";
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
            declarations: [ InternalErrorComponent ],
            providers: [
                { provide: ActivatedRoute,  useValue: route },
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(InternalErrorComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    }

    it('should contain requested ID', () => {
        setupComponent("goober");
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(2);
        expect(pels[0].textContent.includes("internal error")).toBe(true)
        expect(pels[1].textContent.includes('"PDR: ')).toBe(true)
        expect(pels[1].textContent.includes('goober')).toBe(true)
    });

    it('should contain expected content, but with no ID', () => {
        setupComponent(null);
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(2);
        expect(pels[0].textContent.includes("internal error")).toBe(true)
        expect(pels[1].textContent.includes('"PDR: ')).toBe(false)
        expect(pels[1].textContent.includes('goober')).toBe(false)
    });

    it('should prevent injection attacks', () => {
        setupComponent('<a href="badurl">GOOBER</a>');
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p");
        expect(pels.length).not.toBeGreaterThan(2);
        expect(pels[0].textContent.includes("internal error")).toBe(true)
        expect(pels[0].textContent.includes('"PDR: ')).toBe(false)
        pels = cmpel.querySelectorAll("a");
        expect(pels.length).not.toBeGreaterThan(1);
        expect(pels[0].textContent.includes('GOOBER')).toBe(false)
    });
});
