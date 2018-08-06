import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppModule } from './app.module';
import { AppComponent } from './app.component';
import { TransferHttpCacheModule } from '@nguniversal/common';

@NgModule({
    imports: [
        AppModule,
        BrowserModule.withServerTransition({ appId: 'PDR-LandingPage' }),
        TransferHttpCacheModule
    ],
    bootstrap: [ AppComponent ]
})
export class AppBrowserModule { }