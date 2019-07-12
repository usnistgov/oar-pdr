import { Title, Meta } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  APP_INITIALIZER, PLATFORM_ID, APP_ID, Inject,
  CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA
} from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { Collaspe } from './landing/collapseDirective/collapse.directive';
import { TreeModule, FieldsetModule, DialogModule, OverlayPanelModule } from 'primeng/primeng';
import { MenuModule } from 'primeng/menu';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { AppComponent } from './app.component';
import { LandingComponent } from './landing/landing.component';
import { DescriptionComponent } from './landing/description/description.component';
import { MetadataComponent } from './landing/metadata/metadata.component';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { KeyValuePipe } from './landing/keyvalue.pipe';
import { MetadataView } from './landing/metadata/metadataview.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { ErrorComponent, UserErrorComponent } from './landing/error.component';
import { SearchResolve } from './landing/search-service.resolve';
import { SharedModule } from './shared/shared.module';
import { SearchService } from './shared/search-service/index';
import { CommonVarService } from './shared/common-var/index';
import { DatacartComponent } from './datacart/datacart.component';
import { CartService } from "./datacart/cart.service";
import { AppShellNoRenderDirective } from './directives/app-shell-no-render.directive';
import { AppShellRenderDirective } from './directives/app-shell-render.directive';
import { FragmentPolyfillModule } from "./fragment-polyfill.module";
import { DownloadService } from "./shared/download-service/download-service.service";
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ConfirmDialogModule, SelectItem, DropdownModule, ConfirmationService, Message } from 'primeng/primeng';
import { ProgressBarModule } from 'primeng/progressbar';
import { TestDataService } from './shared/testdata-service/testDataService';
import { CommonFunctionService } from './shared/common-function/common-function.service';
import {enableProdMode} from '@angular/core';
import { ModalComponent } from './directives';
import { ModalService } from './shared/modal-service';
import { TaxonomyListService } from './shared/taxonomy-list'
import { ComboBoxComponent } from './shared/combobox/combo-box.component';
import { ComboBoxPipe } from './shared/combobox/combo-box.pipe';

// future
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { ErrorHandler } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';

import { FrameModule } from './frame/frame.module';
import { ConfigModule } from './config/config.module';
import { AppRoutingModule } from './app-routing.module';
import { CustomizationServiceService } from './shared/customization-service/customization-service.service';


enableProdMode();
// used to create fake backend
import { fakeBackendProvider } from './_helpers/fakeBackendInterceptor';
import { LoginComponent } from './login/login.component';
import { ContenteditableModel } from './directives/contenteditable-model.directive';
import { SearchTopicsComponent } from './landing/search-topics/search-topics.component';
import { DataTableModule } from 'primeng/primeng';
import { DescriptionPopupComponent } from './landing/description/description-popup/description-popup.component';
import { AuthorPopupComponent } from './landing/author-popup/author-popup.component';
import { ContactPopupComponent } from './landing/contact-popup/contact-popup.component';

@NgModule({
  declarations: [
    AppComponent,
    LandingAboutComponent, LandingComponent, DatacartComponent,
    Collaspe, MetadataComponent, DescriptionComponent,
    KeyValuePipe, MetadataView, NoidComponent, NerdmComponent,
    ErrorComponent, UserErrorComponent,ComboBoxComponent,ComboBoxPipe,
    AppShellNoRenderDirective, AppShellRenderDirective, LoginComponent, ModalComponent, ContenteditableModel, SearchTopicsComponent, DescriptionPopupComponent, AuthorPopupComponent, ContactPopupComponent
  ],
  imports: [
      HttpClientModule,
      ConfigModule,        // provider for AppConfig
      FrameModule,
      AppRoutingModule,

      FragmentPolyfillModule.forRoot({
          smooth: true
      }),
      FormsModule, ReactiveFormsModule,
      CommonModule, SharedModule, BrowserAnimationsModule, FormsModule, TooltipModule,
      TreeTableModule, TreeModule, MenuModule, FieldsetModule, DialogModule, OverlayPanelModule,
      ButtonModule, ProgressSpinnerModule, ConfirmDialogModule, ProgressBarModule,DataTableModule,
      NgbModule.forRoot()
  ],
  exports: [Collaspe],
  providers: [
    Title,
    Meta,
    SearchService,
    SearchResolve,
    CommonVarService,
    CartService,
    DownloadService,
    TestDataService,
    ConfirmationService,
    CommonFunctionService,
    TaxonomyListService,
    ModalService,
    CustomizationServiceService,

    // provider used to create fake backend
    fakeBackendProvider
  ],
  entryComponents: [
    SearchTopicsComponent, 
    DescriptionPopupComponent, 
    AuthorPopupComponent,
    ContactPopupComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA]
})

export class AppModule {
}


