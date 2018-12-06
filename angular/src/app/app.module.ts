import { Title,Meta } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgModule,APP_INITIALIZER, PLATFORM_ID, APP_ID, Inject,
         CUSTOM_ELEMENTS_SCHEMA,NO_ERRORS_SCHEMA } from '@angular/core';
import { isPlatformBrowser,CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule } from '@angular/common/http'; 
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { Collaspe } from './landing/collapseDirective/collapse.directive';
import { TreeModule, FieldsetModule, DialogModule, OverlayPanelModule } from 'primeng/primeng';
import { MenuModule } from 'primeng/menu';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { LandingComponent } from './landing/landing.component';
import { DescriptionComponent } from './landing/description/description.component';
import { MetadataComponent } from './landing/metadata/metadata.component';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { KeyValuePipe } from './landing/keyvalue.pipe';
import { MetadataView } from './landing/metadata/metadataview.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { ErrorComponent, UserErrorComponent } from './landing/error.component';
// import { SearchResolve } from './landing/search-service.resolve';
import { SharedModule } from './shared/shared.module';
import { SearchService } from './shared/search-service/index';
import { CommonVarService } from './shared/common-var/index';
import { AppConfig } from './shared/config-service/config.service';
import { DatacartComponent} from './datacart/datacart.component';
import { CartService } from "./datacart/cart.service";
import { AppShellNoRenderDirective } from './directives/app-shell-no-render.directive';
import { AppShellRenderDirective } from './directives/app-shell-render.directive';
import { FragmentPolyfillModule } from "./fragment-polyfill.module";
/**
 * Initialize the configs for backend services
 */
const appInitializerFn = (appConfig: AppConfig) => {
  return () => {
    console.log("**** CAlling APP Initialization ***");
    return appConfig.loadAppConfig();
  };
};

@NgModule({
  declarations: [
    AppComponent,
    LandingAboutComponent, LandingComponent,DatacartComponent,
    Collaspe,MetadataComponent, DescriptionComponent,  
    KeyValuePipe, MetadataView, NoidComponent,NerdmComponent,
    ErrorComponent,UserErrorComponent, 
    AppShellNoRenderDirective, AppShellRenderDirective 
  ],
  imports: [
    FragmentPolyfillModule.forRoot({
      smooth: true
  }),
    FormsModule, ReactiveFormsModule,
    AppRoutingModule, HttpClientModule,
    CommonModule, SharedModule, BrowserAnimationsModule, FormsModule,TooltipModule,
    TreeTableModule, TreeModule,MenuModule, FieldsetModule,DialogModule,OverlayPanelModule,
    ButtonModule,
    NgbModule.forRoot()
  ],
  exports: [Collaspe],
  providers: [ Title, Meta, SearchService, CommonVarService,  CartService 
    , AppConfig, {
      provide: APP_INITIALIZER,
      useFactory: appInitializerFn,
      multi: true,
      deps: [AppConfig]
    }  
  ],
  schemas: [ CUSTOM_ELEMENTS_SCHEMA ,NO_ERRORS_SCHEMA]
})

export class AppModule {
  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    @Inject(APP_ID) private appId: string) {
    const platform = isPlatformBrowser(platformId) ?
      'in the browser' : 'on the server';
  }
 }


  