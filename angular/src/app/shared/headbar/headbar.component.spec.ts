import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

import { HeadbarComponent } from './headbar.component';
import { CommonVarService } from '../common-var/common-var.service';


  describe('AppComponent', () => {
    let component: HeadbarComponent;
    let fixture: ComponentFixture<HeadbarComponent>;

    beforeEach(async(() => {
      TestBed.configureTestingModule({
        declarations: [HeadbarComponent]
        ,providers:[ CommonVarService]
        ,imports:[ RouterTestingModule ]
      })
        .compileComponents();
    }));

    beforeEach(() => {
      fixture = TestBed.createComponent(HeadbarComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });
  });

