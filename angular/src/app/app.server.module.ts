import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { ServerModule, ServerTransferStateModule } from '@angular/platform-server';
import { ModuleMapLoaderModule } from '@nguniversal/module-map-ngfactory-loader';
import { AppModule } from './app.module';
import { AppComponent } from './app.component';
import { ServerMetadataTransferModule } from './nerdm/metadatatransfer-server.module';

/**
 * The root module for the server-side application.  
 *
 * Top-level module bits common to both server and browser are imported via the AppModule.
 */
@NgModule({
    imports: [
        BrowserModule.withServerTransition({appId: 'PDR-LandingPageService'}),
        AppModule,
        ServerModule,
        ModuleMapLoaderModule,
        ServerTransferStateModule,
        ServerMetadataTransferModule
    ],
    // Since the bootstrapped component is not inherited from your
    // imported AppModule, it needs to be repeated here.
    bootstrap: [ AppComponent ],
})
export class AppServerModule {}
