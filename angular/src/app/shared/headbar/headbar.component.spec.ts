import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

import { HeadbarComponent } from './headbar.component';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { CartService } from '../../datacart/cart.service';
import { AppConfig } from '../config-service/config.service';

  describe('AppComponent', () => {
    let component: HeadbarComponent;
    let fixture: ComponentFixture<HeadbarComponent>;

    beforeEach(async(() => {
      TestBed.configureTestingModule({
        declarations: [ HeadbarComponent ]
        ,providers:[  AppConfig, CartService]
        ,imports:[ HttpClientModule, RouterTestingModule ]
      })
        .compileComponents();
    }));

    beforeEach(() => {
      fixture = TestBed.createComponent(HeadbarComponent);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    // it('should create the Headbar', async(() => {
    //     const fixture = TestBed.createComponent(HeadbarComponent);
    //     const app = fixture.debugElement.componentInstance;
    //     expect(app).toBeTruthy();
    //   }));
  });

