import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ContactPopupComponent } from './contact-popup.component';
import { FormsModule } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { SharedService } from '../../../shared/shared';

describe('ContactPopupComponent', () => {
  let component: ContactPopupComponent;
  let fixture: ComponentFixture<ContactPopupComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContactPopupComponent ],
      imports: [FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [NgbActiveModal, SharedService]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContactPopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});