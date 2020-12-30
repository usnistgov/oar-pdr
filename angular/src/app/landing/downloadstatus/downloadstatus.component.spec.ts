import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap' ; 
import { DownloadstatusComponent } from './downloadstatus.component';

describe('DownloadstatusComponent', () => {
  let component: DownloadstatusComponent;
  let fixture: ComponentFixture<DownloadstatusComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DownloadstatusComponent ],
      imports: [
        NgbModule.forRoot()
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DownloadstatusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
