import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

import { FootbarComponent } from './footbar.component';

export function main() {
  describe('AppComponent', () => {
    let component: FootbarComponent;
    let fixture: ComponentFixture<FootbarComponent>;

    beforeEach(async(() => {
      TestBed.configureTestingModule({
        declarations: [FootbarComponent]
      })
        .compileComponents();
    }));

    beforeEach(() => {
      fixture = TestBed.createComponent(FootbarComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });
  });
}
