import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { EditControlComponent } from './editcontrol.component';
import { EditStatusComponent } from './editstatus.component';
import { AuthService, createAuthService } from './auth.service';
import { ConfirmationDialogModule } from '../../shared/confirmation-dialog/confirmation-dialog.module';
import { FrameModule } from '../../frame/frame.module';
import { AppConfig } from '../../config/config';

@NgModule({
    declarations: [ EditControlComponent, EditStatusComponent ],
    imports: [ CommonModule, ConfirmationDialogModule, FrameModule ],
    exports: [ EditControlComponent, EditStatusComponent ],
    providers: [
        { provide: AuthService, useFactory: createAuthService, deps: [ AppConfig ] }
    ]
})
export class EditControlModule { }