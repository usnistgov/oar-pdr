import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SearchService } from '../../shared/search-service/index';
import { ResultlistComponent } from './resultlist.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { AppConfig } from '../../config/config'
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { TransferState } from '@angular/platform-browser';
import { DropdownModule } from "primeng/dropdown";
import { FormsModule } from '@angular/forms';
import { InputTextareaModule } from 'primeng/inputtextarea';

describe('ResultlistComponent', () => {
  let component: ResultlistComponent;
  let fixture: ComponentFixture<ResultlistComponent>;
  let plid : Object = "browser";
  let ts : TransferState = new TransferState();
  let cfg : AppConfig = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
        imports: [
            HttpClientTestingModule, 
            BrowserTransferStateModule, 
            DropdownModule,
            FormsModule,
            InputTextareaModule],
        declarations: [ ResultlistComponent ],
        providers: [
            SearchService,
            { provide: AppConfig,       useValue: cfg }
        ]
    })
    .compileComponents();
  });

  beforeEach(() => {
        fixture = TestBed.createComponent(ResultlistComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
  });

  it('should create', () => {
        expect(component).toBeTruthy();
  });
});
