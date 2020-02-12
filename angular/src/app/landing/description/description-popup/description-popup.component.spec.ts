import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { DescriptionModule, DescriptionPopupComponent } from '../description.module';
import { FormsModule } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { GoogleAnalyticsService } from '../../../shared/ga-service/google-analytics.service';

describe('DescriptionPopupComponent', () => {
  let component: DescriptionPopupComponent;
  let fixture: ComponentFixture<DescriptionPopupComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [  ],
      imports: [DescriptionModule, FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [NgbActiveModal, GoogleAnalyticsService]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DescriptionPopupComponent);
    component = fixture.componentInstance;
    component.field = "description";
    component.inputValue = {description: "test"};
    component.title = "description";
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
