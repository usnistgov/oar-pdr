import { NgModule } from '@angular/core';
import { EditControlsComponent } from './edit-controls/edit-controls.component';
import { EditStatusBarComponent } from './edit-status-bar/edit-status-bar.component';
import { ErrorMessageComponent } from './error-message/error-message.component';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { EditControlService } from './edit-control.service';

@NgModule({
  declarations: [
    EditControlsComponent,
    EditStatusBarComponent,
    ErrorMessageComponent
  ],
  imports: [CommonModule, BrowserModule],
  exports: [
    EditControlsComponent,
    EditStatusBarComponent,
    ErrorMessageComponent],
  providers: [
    EditControlService
  ]
})

export class EditControlBarModule {
}
