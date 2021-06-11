import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { TreeTableModule } from 'primeng/treetable';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { DataFilesComponent } from './data-files.component';

/**
 * module that provides support for rendering the listing of data file
 */
@NgModule({
    imports: [
        CommonModule, RouterModule,
        TreeTableModule, OverlayPanelModule, ProgressSpinnerModule
    ],
    declarations: [
        DataFilesComponent
    ],
    providers: [ ],
    exports: [
        DataFilesComponent
    ]
})
export class DataFilesModule { }
