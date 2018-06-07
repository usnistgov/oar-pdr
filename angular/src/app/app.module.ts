import { BrowserModule,Title,DomSanitizer } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgModule,APP_INITIALIZER, PLATFORM_ID, APP_ID, Inject,
         CUSTOM_ELEMENTS_SCHEMA,NO_ERRORS_SCHEMA } from '@angular/core';
import { isPlatformBrowser,CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HttpClient } from '@angular/common/http'; 

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
//import { Ng2StickyModule } from 'ng2-sticky';
import { Collaspe } from './landing/collapseDirective/collapse.directive';
import { ButtonModule, DropdownModule, AccordionModule, PanelMenuModule,MenuItem,AutoCompleteModule,
          MessagesModule, MultiSelectModule, DataTableModule, DataListModule,ContextMenuModule,
          MenuModule,OverlayPanelModule, FieldsetModule, PanelModule ,DialogModule } from 'primeng/primeng';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { LandingComponent } from './landing/landing.component';
import { DescriptionComponent } from './landing/description.component';
import { MetadataComponent } from './landing/metadata/metadata.component';
import { FileDetailsComponent } from './landing/fileDetails/filedetails.component';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { KeyValuePipe } from './landing/keyvalue.pipe';
import { MetadataView } from './landing/metadata/metadataview.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { ErrorComponent,UserErrorComponent } from './landing/error.component';
import { SearchResolve } from './landing/search-service.resolve';
import { SharedModule } from './shared/shared.module';
import { SearchService } from './shared/search-service/index';
import { CommonVarService } from './shared/common-var/index';
import { AppConfig } from './shared/config-service/config.service';
import {TreeTableModule} from 'primeng/treetable';
import { Ng2StickyModule } from 'ng2-sticky';

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
    CommonModule, SharedModule, AccordionModule,AutoCompleteModule,MessagesModule,MultiSelectModule,
    DropdownModule,DataTableModule, DataListModule, PanelMenuModule,DialogModule,
    ContextMenuModule,MenuModule,OverlayPanelModule, FieldsetModule, PanelModule,BrowserAnimationsModule, 
    FormsModule, ButtonModule,
    TreeTableModule,
    Ng2StickyModule,
    NgbModule.forRoot()
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


  