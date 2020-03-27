import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule, DatePipe } from '@angular/common';

import { EditStatusComponent } from './editstatus.component';
import { MetadataUpdateService } from './metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { UpdateDetails, UserDetails } from './interfaces';
import { LandingConstants } from '../constants';
import { AppConfig } from '../../config/config';
import { config, testdata } from '../../../environments/environment';

describe('EditStatusComponent', () => {
    let component : EditStatusComponent;
    let fixture : ComponentFixture<EditStatusComponent>;
    let authsvc : AuthService = new MockAuthService(undefined);
    let cfg : AppConfig = new AppConfig(config);
    let userDetails: UserDetails = {
        'userId': 'dsn1',
        'userName': 'test01',
        'userLastName': 'NIST',
        'userEmail': 'test01@nist.gov'
    }
    let updateDetails: UpdateDetails = {
        'userDetails': userDetails,
        '_updateDate': '2025 April 1'
    }

    let EDIT_MODES = LandingConstants.editModes;

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ CommonModule ],
            declarations: [ EditStatusComponent ],
            providers: [
                UserMessageService, MetadataUpdateService, DatePipe,
                { provide: AuthService, useValue: authsvc },
                { provide: AppConfig, useValue: cfg }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(EditStatusComponent);
        component = fixture.componentInstance;
    }

    beforeEach(async(() => {
        makeComp();
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();
        expect(component.updateDetails).toBe(null);
        expect(component.message).toBe("");
        expect(component.messageColor).toBe("black");
        expect(component.isProcessing).toBeFalsy();

        let cmpel = fixture.nativeElement;
        let bardiv = cmpel.querySelector(".ec-status-bar");
        expect(bardiv).not.toBeNull();
        expect(bardiv.childElementCount).toBe(3);
        expect(bardiv.firstElementChild.tagName).toEqual("SPAN");
        expect(bardiv.firstElementChild.innerHTML).toContain("required field");
        expect(bardiv.firstElementChild.nextElementSibling.tagName).toEqual("SPAN");
    });

    it('showMessage()', () => {
        component.showMessage("Okay, Boomer.", false, "sicklyGreen");
        expect(component.message).toBe("Okay, Boomer.");
        expect(component.messageColor).toBe("sicklyGreen");
        expect(component.isProcessing).toBeFalsy();
        fixture.detectChanges();

        let cmpel = fixture.nativeElement;
        let bardiv = cmpel.querySelector(".ec-status-bar");
        expect(bardiv).not.toBeNull();
        expect(bardiv.firstElementChild.innerHTML).toContain("required field");

        component.showMessage("Wait...", true, "blue");
        expect(component.message).toBe("Wait...");
        expect(component.messageColor).toBe("blue");
        expect(component.isProcessing).toBeTruthy();
        fixture.detectChanges();

        expect(bardiv.firstElementChild.innerHTML).toContain("required field");
    });

    it('showLastUpdate()', () => {
        expect(component.updateDetails).toBe(null);

        component.showLastUpdate(EDIT_MODES.PREVIEW_MODE);
        expect(component.message).toContain("To see any previously");
        fixture.detectChanges();
        let cmpel = fixture.nativeElement;
        let bardiv = cmpel.querySelector(".ec-status-bar");
        expect(bardiv).not.toBeNull();
        expect(bardiv.firstElementChild.innerHTML).toContain("required field");
        
        component.showLastUpdate(EDIT_MODES.EDIT_MODE);
        expect(component.message).toContain('Click on the <i class="faa faa-pencil"></i> button to edit');
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('required field');

        component.setLastUpdateDetails(updateDetails);
        
        component.showLastUpdate(EDIT_MODES.PREVIEW_MODE);
        expect(component.message).toContain("There are un-submitted changes last edited on 2025 April 1");
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('required field');
        component.showLastUpdate(EDIT_MODES.EDIT_MODE);
        expect(component.message).toContain("This record was edited");
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('required field');

        component.showLastUpdate(EDIT_MODES.DONE_MODE);
        expect(component.message).toContain('You can now close this window');
    });


});
