import { NerdmComponent } from './nerdm.component';
import { ComponentFixture, TestBed, waitForAsync as  } from '@angular/core/testing';
import { By }           from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

  describe('NerdmComponent', function () {
    let de: DebugElement;
    let comp: NerdmComponent;
    let fixture: ComponentFixture<NerdmComponent>;
  
    beforeEach(waitForAsync(() => {
      TestBed.configureTestingModule({
        declarations: [ NerdmComponent ]
      })
      .compileComponents();
    }));
  
    beforeEach(() => {
      fixture = TestBed.createComponent(NerdmComponent);
      comp = fixture.componentInstance;
      de = fixture.debugElement.query(By.css('p'));
    });
  
    it('should create component', () => expect(comp).toBeDefined() );
  
    it('should have expected <p> text', () => {
      fixture.detectChanges();
      const p = de.nativeElement;
      expect(p.textContent).toMatch(/JSON-LD/i,
        '<P> should say something about "JSON-LD"');
    });
  });
