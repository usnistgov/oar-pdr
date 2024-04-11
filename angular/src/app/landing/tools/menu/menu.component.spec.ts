import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppConfig } from '../../../config/config'
import { MenuComponent } from './menu.component';
import { TransferState } from '@angular/platform-browser';
import { AngularEnvironmentConfigService } from '../../../config/config.service';
import { testdata } from '../../../../environments/environment';

describe('MenuComponent', () => {
  let component: MenuComponent;
  let fixture: ComponentFixture<MenuComponent>;

  let cfg : AppConfig;
  let plid : Object = "browser";
  let ts : TransferState = new TransferState();
  let md = testdata['test1'];

  beforeEach(async () => {
    cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
    await TestBed.configureTestingModule({
      declarations: [ MenuComponent ],
      providers: [
        { provide: AppConfig,  useValue: cfg }
    ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MenuComponent);
    component = fixture.componentInstance;
    component.record = md;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
