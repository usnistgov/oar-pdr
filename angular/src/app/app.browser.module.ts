import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';

import { NgModule } from '@angular/core';

import { AppModule } from './app.module';

import { AppComponent } from './app.component';

@NgModule({
    imports: [
        AppModule,
        BrowserModule.withServerTransition({ appId: 'PDR-LandingPage' }),
        BrowserTransferStateModule
    ],
    bootstrap: [AppComponent]
})
export class AppBrowserModule { }