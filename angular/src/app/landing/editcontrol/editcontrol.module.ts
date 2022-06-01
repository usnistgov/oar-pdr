import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { EditControlComponent } from './editcontrol.component';
import { EditStatusComponent } from './editstatus.component';
import { AuthService, createAuthService } from './auth.service';
import { ConfirmationDialogModule } from '../../shared/confirmation-dialog/confirmation-dialog.module';
import { FrameModule } from '../../frame/frame.module';
import { ButtonModule } from 'primeng/button';
import { AppConfig } from '../../config/config';
import { HttpClient } from '@angular/common/http';
import { OverlayPanelModule } from 'primeng/overlaypanel';

@NgModule({
    declarations: [ EditControlComponent, EditStatusComponent ],
    imports: [ CommonModule, ConfirmationDialogModule, FrameModule, ButtonModule, OverlayPanelModule ],
    exports: [ EditControlComponent, EditStatusComponent ],
    providers: [
        HttpClient,
        { provide: AuthService, useFactory: createAuthService, deps: [ AppConfig, HttpClient ] }
    ]
})
export class EditControlModule { }
