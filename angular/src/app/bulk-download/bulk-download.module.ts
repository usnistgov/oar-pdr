import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BulkDownloadComponent } from './bulk-download.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ButtonModule } from 'primeng/button';

@NgModule({
    declarations: [BulkDownloadComponent],
    imports: [
        CommonModule,
        BrowserAnimationsModule,
        ButtonModule
    ],
    exports: [ BulkDownloadComponent ]
})
export class BulkDownloadModule { }
