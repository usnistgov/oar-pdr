import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TransferState } from '@angular/platform-browser';

import { MenuModule } from 'primeng/menu';

import { ToolMenuComponent } from './toolmenu.component';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { AppConfig } from '../../config/config'
import { NerdmRes } from '../../nerdm/nerdm';
import { testdata } from '../../../environments/environment';

describe('ToolMenuComponent', () => {
    let component : ToolMenuComponent;
    let fixture : ComponentFixture<ToolMenuComponent>;
    let cfg : AppConfig;
    let plid : Object = "browser";
    let ts : TransferState = new TransferState();

    let setupComponent = function(popup : boolean, md : NerdmRes) {
        cfg = (new AngularEnvironmentConfigService(plid, ts)).getConfig() as AppConfig;
        cfg.locations.pdrSearch = "https://goob.nist.gov/search";
        
        component = null;
        TestBed.configureTestingModule({
            imports: [ CommonModule, MenuModule, BrowserAnimationsModule ],
            declarations: [ ToolMenuComponent ],
            providers: [
                { provide: AppConfig,  useValue: cfg },
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(ToolMenuComponent);
        component = fixture.componentInstance;
        component.record = md;
        component.isPopup = popup;
        fixture.detectChanges();
    }

    it('displays the submenus', () => {
        let md = testdata['test1'];
        setupComponent(false, md);

        expect(component).toBeDefined();
        expect(component.record['@id']).toBe('ark:/88434/mds0000fbk');
        expect(component.isPopup).toBe(false);

        let cmpel = fixture.nativeElement;
        let pels = cmpel.querySelectorAll("p-menu");
        expect(pels.length).toBeGreaterThan(0);
        
    });
});
