import { async, ComponentFixture, TestBed, ComponentFixtureAutoDetect } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';

import { AppConfig } from '../../config/config';
import { ConfirmationDialogService } from '../../shared/confirmation-dialog/confirmation-dialog.service';
import { ConfirmationDialogComponent } from '../../shared/confirmation-dialog/confirmation-dialog.component';
import { UserMessageService } from '../../frame/usermessage.service';
import { MetadataUpdateService } from './metadataupdate.service';
import { AuthService, WebAuthService, MockAuthService } from './auth.service';
import { EditControlComponent } from './editcontrol.component';
import { EditControlModule } from './editcontrol.module';
import { CommonModule, DatePipe } from '@angular/common';

import { config, testdata } from '../../../environments/environment';

describe('EditControlComponent', () => {
    let component : EditControlComponent;
    let fixture : ComponentFixture<EditControlComponent>;
    let cfg : AppConfig = new AppConfig(config);
    let rec = testdata['test1'];
    let authsvc : AuthService = new MockAuthService()

    let makeComp = function() {
        TestBed.configureTestingModule({
            imports: [ EditControlModule, HttpClientModule ],
            declarations: [  ],
            providers: [
                { provide: AppConfig, useValue: cfg },
                { provide: AuthService, useValue: authsvc },
                UserMessageService, MetadataUpdateService, DatePipe
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(EditControlComponent);
        component = fixture.componentInstance;
        component.mdrec = rec;
        // fixture.detectChanges();
    }

    beforeEach(async(() => {
        makeComp();
        component.inBrowser = true;
        fixture.detectChanges();
    }));

    it('should initialize', () => {
        expect(component).toBeDefined();
        expect(component.editMode).toBeFalsy();

        let cmpel = fixture.nativeElement;
        let btns = cmpel.querySelectorAll("button");
        expect(btns.length).toEqual(3);

        let statusdiv = cmpel.querySelector(".ec-status-bar");
        expect(statusdiv).not.toBeNull();
        expect(statusdiv.childElementCount).toBe(2);
    });

    it('can get authorized', async () => {
        expect(component.isAuthorized()).toBeFalsy();
        let authed : boolean = await component.authorizeEditing().toPromise();
        expect(authed).toBeTruthy();
        expect(component.isAuthorized()).toBeTruthy();
    });

    // test startEditing()
    it('startEditing()', async(() => {
        expect(component.editMode).toBeFalsy();
        let cmpel = fixture.nativeElement;
        let edbtn = cmpel.querySelector("#ec-edit-btn") 
        let discbtn = cmpel.querySelector("#ec-discard-btn") 
        let subbtn = cmpel.querySelector("#ec-submit-btn") 
        let qedbtn = cmpel.querySelector("#ec-quited-btn")  
        expect(qedbtn).toBeNull();
        expect(edbtn.disabled).toBeFalsy();
        expect(subbtn.disabled).toBeTruthy();
        expect(discbtn.disabled).toBeTruthy();

        component.startEditing();
        fixture.whenStable().then(() => {
            fixture.detectChanges();
            expect(component.editMode).toBeTruthy();
            
            edbtn = cmpel.querySelector("#ec-edit-btn")     
            discbtn = cmpel.querySelector("#ec-discard-btn")
            subbtn = cmpel.querySelector("#ec-submit-btn")  
            qedbtn = cmpel.querySelector("#ec-quited-btn")  
            expect(qedbtn.disabled).toBeFalsy();
            expect(subbtn.disabled).toBeTruthy();
            expect(discbtn.disabled).toBeFalsy();
            expect(edbtn).toBeNull();
        });

    }));

    // test discardEdits()
    it('discardEdits()', async(() => {
        expect(component.editMode).toBeFalsy();
        let cmpel = fixture.nativeElement;
        let edbtn = cmpel.querySelector("#ec-edit-btn") 

        component.startEditing();
        fixture.whenStable().then(() => {
            fixture.detectChanges();
            expect(component.editMode).toBeTruthy();
            
            edbtn = cmpel.querySelector("#ec-edit-btn")     
            expect(edbtn).toBeNull();

            component.discardEdits();
            fixture.whenStable().then(() => {
                fixture.detectChanges();
                expect(component.editMode).toBeFalsy();
                
                edbtn = cmpel.querySelector("#ec-edit-btn")     
                let discbtn = cmpel.querySelector("#ec-discard-btn") 
                let subbtn = cmpel.querySelector("#ec-submit-btn") 
                let qedbtn = cmpel.querySelector("#ec-quited-btn")
                
                expect(qedbtn).toBeNull();
                expect(edbtn.disabled).toBeFalsy();
                expect(subbtn.disabled).toBeTruthy();
                expect(discbtn.disabled).toBeTruthy();
            });
        });
    }));

    // test saveEdits
    it('saveEdits()', async(() => {
        expect(component.editMode).toBeFalsy();
        let cmpel = fixture.nativeElement;
        let edbtn = cmpel.querySelector("#ec-edit-btn") 

        component.startEditing();
        fixture.whenStable().then(() => {
            fixture.detectChanges();
            expect(component.editMode).toBeTruthy();
            
            edbtn = cmpel.querySelector("#ec-edit-btn")     
            expect(edbtn).toBeNull();

            component.saveEdits();
            fixture.whenStable().then(() => {
                fixture.detectChanges();
                expect(component.editMode).toBeFalsy();
                
                edbtn = cmpel.querySelector("#ec-edit-btn")     
                let discbtn = cmpel.querySelector("#ec-discard-btn") 
                let subbtn = cmpel.querySelector("#ec-submit-btn") 
                let qedbtn = cmpel.querySelector("#ec-quited-btn")
                
                expect(qedbtn).toBeNull();
                expect(edbtn.disabled).toBeFalsy();
                expect(subbtn.disabled).toBeTruthy();
                expect(discbtn.disabled).toBeTruthy();
            });
        });
    }));

    // test pauseEditing
    it('pauseEditing()', async(() => {
        expect(component.editMode).toBeFalsy();
        let cmpel = fixture.nativeElement;
        let edbtn = cmpel.querySelector("#ec-edit-btn") 

        component.startEditing();
        fixture.whenStable().then(() => {
            fixture.detectChanges();
            expect(component.editMode).toBeTruthy();
            
            edbtn = cmpel.querySelector("#ec-edit-btn")     
            expect(edbtn).toBeNull();

            component.pauseEditing();
            fixture.whenStable().then(() => {
                fixture.detectChanges();
                expect(component.editMode).toBeFalsy();
                
                edbtn = cmpel.querySelector("#ec-edit-btn")     
                let discbtn = cmpel.querySelector("#ec-discard-btn") 
                let subbtn = cmpel.querySelector("#ec-submit-btn") 
                let qedbtn = cmpel.querySelector("#ec-quited-btn")
                
                expect(qedbtn).toBeNull();
                expect(edbtn.disabled).toBeFalsy();
                expect(subbtn.disabled).toBeTruthy();
                expect(discbtn.disabled).toBeTruthy();
            });
        });
    }));

    it('showMessage()', () => {
        let cmpel = fixture.nativeElement;
        let edbtn = cmpel.querySelector("#ec-edit-btn") 
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(0);

        component.showMessage("Blah Blah");
        component.showMessage("Yay!", "celebration");
        component.showMessage("Huh?", "bewilderment");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(3);
    });
});

