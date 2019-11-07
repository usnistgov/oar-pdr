import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { EditControlComponent } from './editcontrol.component';
import { AuthService, WebAuthService } from './auth.service';
import { ConfirmationDialogModule } from '../../shared/confirmation-dialog/confirmation-dialog.module';

@NgModule({
    declarations: [ EditControlComponent ],
    imports: [ CommonModule, ConfirmationDialogModule ],
    exports: [ EditControlComponent ],
    providers: [
        { provide: AuthService, useClass: WebAuthService }
    ]
})
export class EditControlModule { }
