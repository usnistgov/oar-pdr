// import { async, ComponentFixture, TestBed } from '@angular/core/testing';
// import { HttpClientModule } from '@angular/common/http';
// import { KeywordComponent } from './keyword.component';
// import { AppConfig } from '../../config/config';
// import { AngularEnvironmentConfigService } from '../../config/config.service';
// import { TransferState } from '@angular/platform-browser';
// import { RouterTestingModule } from '@angular/router/testing';
// import { FormsModule } from '@angular/forms';
// import { DatePipe } from '@angular/common';
// import { ToastrModule } from 'ngx-toastr';
// import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
// import { UserMessageService } from '../../frame/usermessage.service';

// describe('KeywordComponent', () => {
//     let component: KeywordComponent;
//     let fixture: ComponentFixture<KeywordComponent>;
//     let cfg: AppConfig;
//     let plid: Object = "browser";
//     let ts: TransferState = new TransferState();

//     beforeEach(() => {
//         cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
//         cfg.locations.pdrSearch = "https://goob.nist.gov/search";
//         cfg.status = "Unit Testing";
//         cfg.appVersion = "2.test";
        
//         TestBed.configureTestingModule({
//             imports: [FormsModule, HttpClientModule, RouterTestingModule, ToastrModule.forRoot()],
//             declarations: [KeywordComponent],
//             providers: [
//                 MetadataUpdateService, UserMessageService, DatePipe,
//                 { provide: AppConfig, useValue: cfg }]
//         })
//             .compileComponents();
//     });

//     beforeEach(() => {
//         let record: any = require('../../../assets/sampleRecord.json');
//         fixture = TestBed.createComponent(KeywordComponent);
//         component = fixture.componentInstance;
//         component.record = record;
//         fixture.detectChanges();
//     });

//     it('should create', () => {
//         expect(component).toBeTruthy();
//     });
// });
