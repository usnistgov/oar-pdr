import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { LandingComponent } from './landing.component';
import { DescriptionComponent } from './description/description.component';
import { MetadataComponent } from './metadata/metadata.component';
import { MetadataView } from './metadata/metadataview.component';
import { NoidComponent } from './noid.component';
import { NerdmComponent } from './nerdm.component';
import { Collaspe } from './collapseDirective/collapse.directive';
import { KeyValuePipe } from './keyvalue.pipe';

import { SharedModule } from '../shared/shared.module';
import { TreeModule, FieldsetModule, DialogModule, OverlayPanelModule,
         ConfirmDialogModule, MenuModule } from 'primeng/primeng';
import { TreeTableModule } from 'primeng/treetable';

/**
 * a module supporting the legacy landing component in a compatibility mode
 */
@NgModule({
    imports: [
        SharedModule, 
        TreeModule, FieldsetModule, DialogModule, OverlayPanelModule, TreeTableModule,
        ConfirmDialogModule, MenuModule
    ],
    declarations: [
        LandingComponent, Collaspe, 
        DescriptionComponent,
        MetadataComponent,
        MetadataView,
        NoidComponent, 
        NerdmComponent,
        KeyValuePipe
    ],
    exports: [
        LandingComponent,
        DescriptionComponent,
        MetadataComponent,
        MetadataView,
        NoidComponent,
        NerdmComponent,
        Collaspe
    ],
    providers: []
})
export class LandingModule { }
