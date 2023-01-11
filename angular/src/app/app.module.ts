import { NgModule }    from '@angular/core';
import { Title, Meta } from '@angular/platform-browser';
import {
    APP_INITIALIZER, PLATFORM_ID, APP_ID, Inject,
    CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA
} from '@angular/core';
import { enableProdMode } from '@angular/core';
import { ErrorHandler } from '@angular/core';

import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { BrowserModule, BrowserTransferStateModule } from '@angular/platform-browser';
import { AppRoutingModule } from './app-routing.module';
import { DatePipe } from '@angular/common';

import { ToastrModule } from 'ngx-toastr';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';
import { LandingPageModule } from './landing/landingpage.module';
import { LandingAboutModule } from './landingAbout/landingAbout.module';
import { SharedModule } from './shared/shared.module';
import { FragmentPolyfillModule } from "./fragment-polyfill.module";
import { ErrorsModule, AppErrorHandler } from './errors/errors.module';
import { FrameModule } from './frame/frame.module';
import { ConfigModule } from './config/config.module';
import { DatacartModule } from './datacart/datacart.module';
import { DirectivesModule } from './directives/directives.module';
import { MetricsModule } from './metrics/metrics.module';

import { ErrorComponent, UserErrorComponent } from './landing/error.component';
import { ModalComponent } from './directives';
import { ComboBoxComponent } from './shared/combobox/combo-box.component';
import { SearchTopicsComponent } from './landing/topic/topic-popup/search-topics.component';
import { DescriptionPopupComponent } from './landing/description/description-popup/description-popup.component';
import { AuthorPopupComponent } from './landing/author/author-popup/author-popup.component';
import { ContactPopupComponent } from './landing/contact/contact-popup/contact-popup.component';
import { GoogleAnalyticsService} from "./shared/ga-service/google-analytics.service";
import { fakeBackendProvider } from './_helpers/fakeBackendInterceptor';
import { PanelModule } from 'primeng/panel';
import { RPAModule } from './rpa/rpa.module';

enableProdMode();

/**
 * The Landing Page Service Application
 */
@NgModule({
    declarations: [
        AppComponent
    ],
    imports: [
        ConfigModule,
        FrameModule,
        ErrorsModule,
        LandingPageModule,
        AppRoutingModule,
        LandingAboutModule,
        DirectivesModule,
        DatacartModule,
        MetricsModule,
        RPAModule,
        SharedModule.forRoot(),
        // FragmentPolyfillModule.forRoot({
        //     smooth: true
        // }),
        HttpClientModule, FormsModule, ReactiveFormsModule,
        CommonModule, BrowserAnimationsModule, FormsModule,
        ToastrModule.forRoot({
            toastClass: 'toast toast-bootstrap-compatibility-fix'
        }),
        PanelModule,
        NgbModule
    ],
    exports: [],
    providers: [
        AppErrorHandler,
        { provide: ErrorHandler, useClass: AppErrorHandler },
        GoogleAnalyticsService,
        // fakeBackendProvider,
        DatePipe
    ],
    schemas: [CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA]
})

export class AppModule {
    // We inject the service here to keep it alive whole time
    constructor(protected _googleAnalyticsService: GoogleAnalyticsService) { } 
}


