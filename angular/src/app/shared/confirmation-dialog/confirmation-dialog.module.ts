import { NgModule } from '@angular/core';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { ConfirmationDialogService } from './confirmation-dialog.service';
import { ConfirmationDialogComponent } from './confirmation-dialog.component';

@NgModule({
    declarations: [ ConfirmationDialogComponent ],
    imports: [ NgbModule ],
    exports: [ ConfirmationDialogComponent ],
    providers: [
        ConfirmationDialogService
    ],
    entryComponents: [ ConfirmationDialogComponent ]
})
export class ConfirmationDialogModule { }
