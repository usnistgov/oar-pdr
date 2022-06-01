import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap' ; 
import { DownloadstatusComponent } from './downloadstatus.component';
import { DataCartStatus, DataCartStatusLookup, DataCartStatusItem, DataCartStatusData, stringifyCart, parseCartStatus } from '../../datacart/cartstatus';

let fakecoll: DataCartStatusLookup = { "goob/gurn": { itemId: "gurn", displayName: "gurnDisplay", isInUse:true, downloadPercentage: 10 }};

describe('DownloadstatusComponent', () => {
  let component: DownloadstatusComponent;
  let fixture: ComponentFixture<DownloadstatusComponent>;
  let sample: DataCartStatusLookup = null;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DownloadstatusComponent ],
      imports: [
        NgbModule
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DownloadstatusComponent);
    sample = <DataCartStatusLookup>JSON.parse(JSON.stringify(fakecoll));
    component = fixture.componentInstance;
    component.inBrowser = true;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('showDownloadStatus', () => {
    component.dataCartStatus = new DataCartStatus("cartStatus", sample);
    expect(component.showDownloadStatus).toBeTruthy();
  });

  it('removeStatusItem', () => {
    component.dataCartStatus = new DataCartStatus("cartStatus", sample);
    component.dataCartStatus.save();
    expect(component.dataCartStatus.findStatusById('goob/gurn')).toBeTruthy();
    component.removeStatusItem('goob/gurn');
    expect(component.dataCartStatus.findStatusById('goob/gurn')).toBeFalsy();
  });
});
