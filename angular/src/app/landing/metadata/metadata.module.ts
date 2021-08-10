import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { FieldsetModule } from 'primeng/fieldset';
import { ButtonModule } from 'primeng/button';

import { MetadataComponent } from './metadata.component'
import { MetadataView } from './metadataview.component'

/**
 * module that provides interfaces for accessing and visualizing the resource's metadata in various formats
 */
@NgModule({
    imports: [
        CommonModule, BrowserAnimationsModule, FieldsetModule, ButtonModule
    ],
    declarations: [
        MetadataComponent, MetadataView
    ],
    providers: [ ],
    exports: [
        MetadataComponent, MetadataView
    ]
})
export class MetadataModule { }

export {
    MetadataComponent, MetadataView
};
