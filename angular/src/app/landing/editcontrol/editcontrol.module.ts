import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { EditControlComponent } from './editcontrol.component';
import { AuthService, WebAuthService } from './auth.service';
import { ConfirmationDialogModule } from '../../shared/confirmation-dialog/confirmation-dialog.module';
import { FrameModule } from '../../frame/frame.module';

@NgModule({
    declarations: [ EditControlComponent ],
    imports: [ CommonModule, ConfirmationDialogModule, FrameModule ],
    exports: [ EditControlComponent ],
    providers: [
        { provide: AuthService, useClass: WebAuthService }
    ]
})
export class EditControlModule { }
