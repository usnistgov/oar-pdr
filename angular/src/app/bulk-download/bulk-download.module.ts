import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BulkDownloadComponent } from './bulk-download.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

@NgModule({
    declarations: [BulkDownloadComponent],
    imports: [
        CommonModule,
        BrowserAnimationsModule
    ],
    exports: [ BulkDownloadComponent ]
})
export class BulkDownloadModule { }
