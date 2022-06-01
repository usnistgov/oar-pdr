import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { FieldsetModule } from 'primeng/fieldset';
import { ButtonModule } from 'primeng/button';

import { AboutdatasetComponent } from './aboutdataset.component';

import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { VersionModule } from '../version/version.module';
import { FacilitatorsModule } from '../facilitators/facilitators.module';

/**
 * module that provides interfaces for accessing and visualizing the resource's metadata in various formats
 */
@NgModule({
    imports: [
        CommonModule, 
        BrowserAnimationsModule, 
        FieldsetModule, 
        ButtonModule, 
        NgxJsonViewerModule, 
        VersionModule,
        FacilitatorsModule
    ],
    declarations: [
        AboutdatasetComponent
    ],
    providers: [ ],
    exports: [
        AboutdatasetComponent
    ]
})
export class AboutdatasetModule { }

export {
    AboutdatasetComponent
};
