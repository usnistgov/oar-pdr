import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { By }           from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { MetadataView } from './metadataview.component';
import { MetadataModule } from './metadata.module';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { testdata } from '../../../environments/environment';
  
describe('MetadataViewComponent', function () {
    let de: DebugElement;
    let comp: MetadataView;
    let fixture: ComponentFixture<MetadataView>;
    let rec : NerdmRes = testdata['test1'];

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            imports: [ MetadataModule ],
        }).compileComponents();
    }));
  
    beforeEach(() => {
        fixture = TestBed.createComponent(MetadataView);
        comp = fixture.componentInstance;
        comp.entry = rec;
        fixture.detectChanges();
        de = fixture.debugElement.query(By.css('p'));
    });
  
    it('should create', () => {
        expect(comp).toBeTruthy();
        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("legend");
        expect(el).toBeTruthy();
        expect(el.textContent).toContain("@context");
    });
});

