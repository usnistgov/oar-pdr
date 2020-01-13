import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule, DatePipe } from '@angular/common';

import { EditStatusComponent } from './editstatus.component';
import { MetadataUpdateService } from './metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';
import { AuthService, WebAuthService, MockAuthService } from '../editcontrol/auth.service';
import { UpdateDetails, UserDetails } from './interfaces';

describe('EditStatusComponent', () => {
    let component : EditStatusComponent;
    let fixture : ComponentFixture<EditStatusComponent>;
    let authsvc : AuthService = new MockAuthService(undefined);
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

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ CommonModule ],
            declarations: [ EditStatusComponent ],
            providers: [
                UserMessageService, MetadataUpdateService, DatePipe,
                { provide: AuthService, useValue: authsvc }
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
        expect(bardiv.childElementCount).toBe(2);
        expect(bardiv.firstElementChild.tagName).toEqual("SPAN");
        expect(bardiv.firstElementChild.innerHTML).toEqual("");
        expect(bardiv.firstElementChild.nextElementSibling.tagName).toEqual("DIV");
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
        expect(bardiv.firstElementChild.innerHTML).toEqual("Okay, Boomer.");

        component.showMessage("Wait...", true, "blue");
        expect(component.message).toBe("Wait...");
        expect(component.messageColor).toBe("blue");
        expect(component.isProcessing).toBeTruthy();
        fixture.detectChanges();

        expect(bardiv.firstElementChild.innerHTML).toEqual("Wait...");
    });

    it('showLastUpdate()', () => {
        expect(component.updateDetails).toBe(null);

        component.showLastUpdate(false);
        expect(component.message).toContain("To see any previously");
        fixture.detectChanges();
        let cmpel = fixture.nativeElement;
        let bardiv = cmpel.querySelector(".ec-status-bar");
        expect(bardiv).not.toBeNull();
        expect(bardiv.firstElementChild.innerHTML).toContain("To see any previously");
        
        component.showLastUpdate(true);
        expect(component.message).toContain('Click on the <i class="faa faa-pencil"></i> button to edit');
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('<i class="faa faa-undo"></i> button to discard the change');

        component.setLastUpdateDetails(updateDetails);
        
        component.showLastUpdate(false);
        expect(component.message).toContain("There are un-submitted changes last edited on 2025 April 1");
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('There are un-submitted changes last edited');
        component.showLastUpdate(true);
        expect(component.message).toContain("This record was edited");
        fixture.detectChanges();
        expect(bardiv.firstElementChild.innerHTML).toContain('This record was edited by test01 NIST on 2025 April 1');
    });


});
