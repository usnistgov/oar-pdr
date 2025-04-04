import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BulkDownloadComponent } from './bulk-download.component';

@NgModule({
  declarations: [BulkDownloadComponent],
  imports: [
    CommonModule
  ],
  exports: [ BulkDownloadComponent ]
})
export class BulkDownloadModule { }
