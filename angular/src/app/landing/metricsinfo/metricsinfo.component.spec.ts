import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MetricsinfoComponent } from './metricsinfo.component';

describe('MetricsinfoComponent', () => {
  let component: MetricsinfoComponent;
  let fixture: ComponentFixture<MetricsinfoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MetricsinfoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MetricsinfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
