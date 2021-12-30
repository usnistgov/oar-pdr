import { NgModule, ModuleWithProviders } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SearchService } from './search-service/index';
import { DownloadService } from "./download-service/download-service.service";
import { ComboBoxComponent } from './combobox/combo-box.component';
import { ComboBoxPipe } from './combobox/combo-box.pipe';
import { ConfirmationDialogService } from './confirmation-dialog/confirmation-dialog.service';
import { NotificationService } from './notification-service/notification.service';

/**
 * Do not specify providers for modules that might be imported by a lazy loaded module.
 */

@NgModule({
    imports: [
        CommonModule, RouterModule, FormsModule
    ],
    exports: [
        ComboBoxComponent, ComboBoxPipe
    ],
    providers: [
        DownloadService, ConfirmationDialogService, NotificationService
    ],
    declarations: [
        ComboBoxComponent, ComboBoxPipe
    ]
})
export class SharedModule {
    static forRoot(): ModuleWithProviders<SharedModule> {
        return {
            ngModule: SharedModule,
            providers: [SearchService]
        };
    }
}

export { ComboBoxComponent, ComboBoxPipe, DownloadService, ConfirmationDialogService, NotificationService };

