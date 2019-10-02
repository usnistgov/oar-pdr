import { Title, Meta } from '@angular/platform-browser';
import {
  APP_INITIALIZER, PLATFORM_ID, APP_ID, Inject,
  CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA
} from '@angular/core';

import { SearchResolve } from './landing/search-service.resolve';
import { AppShellRenderDirective } from './directives/app-shell-render.directive';
import { enableProdMode } from '@angular/core';
import { ComboBoxPipe } from './shared/combobox/combo-box.pipe';
import { ErrorHandler } from '@angular/core';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { FragmentPolyfillModule } from "./fragment-polyfill.module";
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ConfirmDialogModule, SelectItem, DropdownModule, ConfirmationService, Message } from 'primeng/primeng';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastrModule } from 'ngx-toastr';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FrameModule } from './frame/frame.module';
import { ConfigModule } from './config/config.module';
import { AppRoutingModule } from './app-routing.module';
import { DataTableModule } from 'primeng/primeng';
import { ContenteditableModel } from './directives/contenteditable-model.directive';

import { ErrorComponent, UserErrorComponent } from './landing/error.component';
import { DatacartComponent } from './datacart/datacart.component';
import { ModalComponent } from './directives';
import { ComboBoxComponent } from './shared/combobox/combo-box.component';
import { AppComponent } from './app.component';
import { LandingPageModule } from './landingPage/landingPage.module';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { SearchTopicsComponent } from './landing/search-topics/search-topics.component';
import { DescriptionPopupComponent } from './landing/description/description-popup/description-popup.component';
import { AuthorPopupComponent } from './landing/author-popup/author-popup.component';
import { ConfirmationDialogService } from './shared/confirmation-dialog/confirmation-dialog.service';
import { ConfirmationDialogComponent } from './shared/confirmation-dialog/confirmation-dialog.component';
import { SharedModule } from './shared/shared.module';
import { CommonVarService } from './shared/common-var/index';
import { CartService } from "./datacart/cart.service";
import { AppShellNoRenderDirective } from './directives/app-shell-no-render.directive';
import { ModalService } from './shared/modal-service';
import { TaxonomyListService } from './shared/taxonomy-list'
import { DownloadService } from "./shared/download-service/download-service.service";
import { TestDataService } from './shared/testdata-service/testDataService';
import { CommonFunctionService } from './shared/common-function/common-function.service';
import { CustomizationServiceService } from './shared/customization-service/customization-service.service';
import { GoogleAnalyticsService} from "./shared/ga-service/google-analytics.service";
import { GoogleAnalyticsServiceMock} from "./shared/ga-service/google-analytics.service.mock";
import { ContactPopupComponent } from './landing/contact-popup/contact-popup.component';
import { NotificationService } from './shared/notification-service/notification.service';
import { DatePipe } from '@angular/common';

// used to create fake backend
import { fakeBackendProvider } from './_helpers/fakeBackendInterceptor';

@NgModule({
  declarations: [
    AppComponent,
    LandingAboutComponent, DatacartComponent,
    ErrorComponent, UserErrorComponent,ComboBoxComponent,ComboBoxPipe,
    AppShellNoRenderDirective, AppShellRenderDirective, ModalComponent, ContenteditableModel, SearchTopicsComponent, DescriptionPopupComponent, AuthorPopupComponent, ContactPopupComponent,
    ConfirmationDialogComponent
  ],
  imports: [
      HttpClientModule,
      ConfigModule,        // provider for AppConfig
      FrameModule,
      LandingPageModule,
      AppRoutingModule,
      FragmentPolyfillModule.forRoot({
          smooth: true
      }),
      FormsModule, ReactiveFormsModule,
      CommonModule, SharedModule, BrowserAnimationsModule, FormsModule, TooltipModule,
      ButtonModule, ProgressSpinnerModule, ProgressBarModule,
      ToastrModule.forRoot({
        toastClass: 'toast toast-bootstrap-compatibility-fix'
      }), NgbModule.forRoot()
  ],
  exports: [],
  providers: [
    Title,
    Meta,
    CommonVarService,
    CartService,
    DownloadService,
    TestDataService,
    ConfirmationService,
    CommonFunctionService,
    TaxonomyListService,
    ModalService,
    CustomizationServiceService,
    GoogleAnalyticsService,
    GoogleAnalyticsServiceMock,
    ConfirmationDialogService,
    NotificationService,
    DatePipe,
    // provider used to create fake backend
    fakeBackendProvider
  ],
  entryComponents: [
    SearchTopicsComponent, 
    DescriptionPopupComponent, 
    AuthorPopupComponent,
    ContactPopupComponent,
    ConfirmationDialogComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA]
})

export class AppModule {
  constructor(protected _googleAnalyticsService: GoogleAnalyticsService) { } // We inject the service here to keep it alive whole time
}


