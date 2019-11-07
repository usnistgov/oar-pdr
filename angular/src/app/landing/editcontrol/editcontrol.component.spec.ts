import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';

import { AppConfig } from '../../config/config';
import { ConfirmationDialogService } from '../../shared/confirmation-dialog/confirmation-dialog.service';
import { ConfirmationDialogComponent } from '../../shared/confirmation-dialog/confirmation-dialog.component';
import { UserMessageService } from '../../frame/usermessage.service';
import { MetadataUpdateService } from './metadataupdate.service';
import { AuthService, WebAuthService, MockAuthService } from './auth.service';
import { EditControlComponent } from './editcontrol.component';
import { EditControlModule } from './editcontrol.module';

import { config, testdata } from '../../../environments/environment';

fdescribe('EditControlComponent', () => {
    let component : EditControlComponent;
    let fixture : ComponentFixture<EditControlComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec = testdata['test1'];
    let authsvc : AuthService = new MockAuthService(rec)

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ EditControlModule, HttpClientModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc },
                UserMessageService, MetadataUpdateService
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(EditControlComponent);
        component = fixture.componentInstance;
        component.mdrec = rec;
        // fixture.detectChanges();
    }

    beforeEach(async(() => {
        makeComp();
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();

        let cmpel = fixture.nativeElement;
        let btns = cmpel.querySelectorAll("button");
        expect(btns.length).toEqual(3);
    });

    it('can get authorized', async () => {
        expect(component.isAuthorized()).toBeFalsy();
        let authed : boolean = await component.authorizeEditing().toPromise();
        expect(authed).toBeTruthy();
        expect(component.isAuthorized()).toBeTruthy();
    });
});

