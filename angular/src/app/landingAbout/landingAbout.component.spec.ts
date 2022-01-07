import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import { LandingAboutComponent } from './landingAbout.component';


  describe('LandingAboutComponent', () => {
    let component: LandingAboutComponent;
    let fixture: ComponentFixture<LandingAboutComponent>;
    let comp: LandingAboutComponent;
    let de: DebugElement;

    beforeEach(waitForAsync(() => {
      TestBed.configureTestingModule({
          declarations: [LandingAboutComponent],
          imports: [ RouterTestingModule ],
          providers: [ ]
      })
        .compileComponents();
    }));

    beforeEach(() => {
      fixture = TestBed.createComponent(LandingAboutComponent);
      comp = fixture.componentInstance;
      de = fixture.debugElement.query(By.css('p'));
    });

   // it('should create component', () => expect(comp).toBeDefined());
   it('should create the comp', waitForAsync(() => {
    const fixture = TestBed.createComponent(LandingAboutComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  }));
    it('should have expected <p> text', () => {
      fixture.detectChanges();
      const p = de.nativeElement;
      expect(p.textContent).toMatch(/NIST Public Data Repository/i,
        '<P> should say something about "NIST Public Data Repository"');
    });

    it('should have proper label', () => {
      fixture.detectChanges();
      de = fixture.debugElement.query(By.css('.labelStyle'));
      const label = de.nativeElement;
      expect(label.textContent).toEqual('About Public Data Repository');
    });

  });
