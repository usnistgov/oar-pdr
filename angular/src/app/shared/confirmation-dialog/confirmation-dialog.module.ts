import { NgModule } from '@angular/core';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { CommonModule } from '@angular/common';  

import { ConfirmationDialogService } from './confirmation-dialog.service';
import { ConfirmationDialogComponent } from './confirmation-dialog.component';

@NgModule({
    declarations: [ConfirmationDialogComponent],
    imports: [NgbModule, CommonModule],
    exports: [ConfirmationDialogComponent],
    providers: [
        ConfirmationDialogService
    ]
})
export class ConfirmationDialogModule { }
