import { MetadataView } from './metadataview.component';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By }           from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

  describe('MetadataViewComponent', function () {
    let de: DebugElement;
    let comp: MetadataView;
    let fixture: ComponentFixture<MetadataView>;
  
    beforeEach(async(() => {
      TestBed.configureTestingModule({
        declarations: [ MetadataView ]
      })
      .compileComponents();
    }));
  
    beforeEach(() => {
      fixture = TestBed.createComponent(MetadataView);
      comp = fixture.componentInstance;
      de = fixture.debugElement.query(By.css('p'));
    });
  
    
  });

