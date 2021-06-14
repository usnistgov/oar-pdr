import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { DatePipe }     from '@angular/common';
import { ButtonModule } from 'primeng/button';

import { NerdmModule } from '../nerdm/nerdm.module';
import { LandingPageComponent } from './landingpage.component';
import { LandingBodyComponent } from './landingbody.component';
import { SectionsModule } from './sections/sections.module';
import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { EditControlModule } from './editcontrol/editcontrol.module';
import { ToolsModule } from './tools/tools.module';
import { CitationModule } from './citation/citation.module';
import { DoneComponent } from './done/done.component';
import { DownloadstatusComponent } from './downloadstatus/downloadstatus.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

/**
 * A module supporting the complete display of landing page content associated with 
 * a resource identifier
 */
@NgModule({
    imports: [
        CommonModule,
        ButtonModule,
        NerdmModule,    // provider for MetadataService (which depends on AppConfig)
        EditControlModule,
        ToolsModule,
        CitationModule,
        SectionsModule,
        NgbModule
    ],
    declarations: [
        LandingPageComponent, DoneComponent, DownloadstatusComponent, LandingBodyComponent
    ],
    providers: [
        MetadataUpdateService, DatePipe
    ],
    exports: [
        LandingPageComponent, DoneComponent, DownloadstatusComponent, LandingBodyComponent
    ]
})
export class LandingPageModule { }

export { LandingPageComponent };
    
