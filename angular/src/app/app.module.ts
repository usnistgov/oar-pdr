import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgModule,APP_INITIALIZER } from '@angular/core';

import {ButtonModule} from 'primeng/primeng';
import { AppComponent } from './app.component';
import { PLATFORM_ID, APP_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { AppRoutingModule } from './app-routing.module';
import { LandingAboutComponent } from './landingabout/landingabout.component';

import { CUSTOM_ELEMENTS_SCHEMA,NO_ERRORS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';


import { SharedModule } from './shared/shared.module';
import { LandingComponent } from './landing/landing.component';
import { DescriptionComponent } from './landing/description.component';
import { MetadataComponent } from './landing/metadata/metadata.component';
import { FileDetailsComponent } from './landing/fileDetails/filedetails.component';
//import { Ng2StickyModule } from 'ng2-sticky';
import { Collaspe } from './landing/collapseDirective/collapse.directive';
//import { SanitizeHtmlDirective } from './landing/sanitizeHtml.directive';
import { KeyValuePipe } from './landing/keyvalue.pipe';
import { MetadataView } from './landing/metadata/metadataview.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';

import { SearchService } from './shared/search-service/index';
import { SearchResolve } from './landing/search-service.resolve';
import { CommonVarService } from './shared/common-var/index';
import { DropdownModule, AccordionModule, TreeModule,PanelMenuModule,MenuItem, TreeNode, AutoCompleteModule,
  MessagesModule, MultiSelectModule, DataTableModule, DataListModule,ContextMenuModule,
  MenuModule,OverlayPanelModule, FieldsetModule, PanelModule ,DialogModule} from 'primeng/primeng';

import { Title,DomSanitizer } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
// import { SimilarsComponent } from './landing/similars.component';
import { HttpClientModule } from '@angular/common/http'; 
import { HttpModule } from '@angular/http';
import {NgbModule} from '@ng-bootstrap/ng-bootstrap';

import { ErrorComponent,UserErrorComponent } from './landing/error.component';
import { AppConfig } from './shared/config-service/config.service';

const appInitializerFn = (appConfig: AppConfig) => {
  return () => {
    return appConfig.loadAppConfig();
  };
};
@NgModule({
  declarations: [
    AppComponent,
    LandingAboutComponent,
    LandingComponent,
    // SimilarsComponent,
    //SanitizeHtmlDirective,
    Collaspe,MetadataComponent,FileDetailsComponent,
    DescriptionComponent,  KeyValuePipe, MetadataView, NoidComponent,NerdmComponent,
    ErrorComponent,UserErrorComponent 
  ],
  imports: [
    //BrowserModule,
    BrowserModule.withServerTransition({ appId: 'PDR-LandingPage' }),
    FormsModule,
    ReactiveFormsModule,
    AppRoutingModule,

    HttpClientModule,
    HttpModule,

    CommonModule, SharedModule, AccordionModule,AutoCompleteModule,MessagesModule,MultiSelectModule,
    DropdownModule,DataTableModule, DataListModule,TreeModule, PanelMenuModule,DialogModule,
    ContextMenuModule,MenuModule,OverlayPanelModule,
     FieldsetModule, PanelModule,BrowserAnimationsModule, FormsModule, ButtonModule
     ,NgbModule.forRoot()
   
  ],
  exports: [Collaspe],
  providers: [ Title, SearchService,SearchResolve, CommonVarService
    , AppConfig, {
      provide: APP_INITIALIZER,
      useFactory: appInitializerFn,
      multi: true,
      deps: [AppConfig]
    }  
  ],
  bootstrap: [AppComponent],
  schemas: [ CUSTOM_ELEMENTS_SCHEMA ,NO_ERRORS_SCHEMA]

})

export class AppModule {
  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    @Inject(APP_ID) private appId: string) {
    const platform = isPlatformBrowser(platformId) ?
      'in the browser' : 'on the server';
    console.log(`Running ${platform} with appId=${appId}`);
  }
  
 }


  