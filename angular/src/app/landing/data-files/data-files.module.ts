import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { TreeTableModule } from 'primeng/treetable';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { BadgeModule } from 'primeng/badge';

import { DataFilesComponent } from './data-files.component';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';

/**
 * module that provides support for rendering the listing of data file
 */
@NgModule({
    imports: [
        CommonModule, RouterModule, BadgeModule, ButtonModule, InputTextModule,
        TreeTableModule, OverlayPanelModule, ProgressSpinnerModule, FormsModule,
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
