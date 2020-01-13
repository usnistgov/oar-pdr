import { NgModule } from '@angular/core';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { AppModule } from './app.module';
import { AppComponent } from './app.component';
import { BrowserMetadataTransferModule } from './nerdm/metadatatransfer-browser.module';

@NgModule({
    imports: [
        BrowserModule.withServerTransition({ appId: 'PDR-LandingPageService' }),
        BrowserAnimationsModule,
        AppModule,
        BrowserTransferStateModule,
        BrowserMetadataTransferModule
    ],
    bootstrap: [ AppComponent ]
})
export class AppBrowserModule { }
