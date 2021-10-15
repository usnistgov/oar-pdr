import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { DatePipe }     from '@angular/common';
import { ButtonModule } from 'primeng/button';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { NerdmModule } from '../nerdm/nerdm.module';
import { LandingPageComponent } from './landingpage.component';
import { LandingBodyComponent } from './landingbody.component';
import { NoidComponent } from './noid.component';
import { NerdmComponent } from './nerdm.component';
import { SectionsModule } from './sections/sections.module';
import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { EditControlModule } from './editcontrol/editcontrol.module';
import { ToolsModule } from './tools/tools.module';
import { CitationModule } from './citation/citation.module';
import { DoneComponent } from './done/done.component';
import { DownloadstatusComponent } from './downloadstatus/downloadstatus.component';
import { TaxonomyListService } from '../shared/taxonomy-list'
import { ErrorComponent, UserErrorComponent } from './error.component';
import { MetricsinfoComponent } from './metricsinfo/metricsinfo.component';

/**
 * A module supporting the complete display of landing page content associated with 
 * a resource identifier
 */
@NgModule({
    imports: [
        CommonModule,
        ButtonModule,
        NgbModule,
        NerdmModule,    // provider for MetadataService (which depends on AppConfig)
        EditControlModule,
        ToolsModule,
        CitationModule,
        SectionsModule
    ],
    declarations: [
        LandingPageComponent, LandingBodyComponent, DoneComponent, DownloadstatusComponent,
        ErrorComponent, UserErrorComponent, NoidComponent, NerdmComponent, MetricsinfoComponent
    ],
    providers: [
        MetadataUpdateService, TaxonomyListService, DatePipe
    ],
    exports: [
        LandingPageComponent, LandingBodyComponent, DoneComponent, DownloadstatusComponent,
        ErrorComponent, UserErrorComponent, NoidComponent, NerdmComponent
    ]
})
export class LandingPageModule { }

export { LandingPageComponent, LandingBodyComponent, NoidComponent, NerdmComponent };
    
