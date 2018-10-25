import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../shared.module';
import { FootbarComponent } from './footbar.component';

  describe('FootbarComponent', () => {
    let component: FootbarComponent;
    let fixture: ComponentFixture<FootbarComponent>;

    beforeEach(async(() => {
      TestBed.configureTestingModule({
        declarations: [FootbarComponent]
        , imports:[ RouterTestingModule ]
      })
        .compileComponents();
    }));

    beforeEach(() => {
      fixture = TestBed.createComponent(FootbarComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should create the comp', async(() => {
        const fixture = TestBed.createComponent(FootbarComponent);
        const app = fixture.debugElement.componentInstance;
        expect(app).toBeTruthy();
      }));
  });
 
