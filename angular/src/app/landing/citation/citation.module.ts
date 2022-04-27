import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { SharedModule } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';

import { CitationDescriptionComponent, CitationPopupComponent } from './citation.component'

/**
 * A module providing components for display citation information for a data resource
 *
 * Two components are provided for displaying this information:
 *  * CitationDescriptionComponent -- a component that display the information in a panel
 *  * CitationPopupComponent -- a component that wraps the description in a pop-up widget
 */
@NgModule({
    imports: [
        CommonModule, ButtonModule, DialogModule, SharedModule, BrowserAnimationsModule
    ],
    declarations: [
        CitationDescriptionComponent, CitationPopupComponent
    ],
    exports: [
        CitationDescriptionComponent, CitationPopupComponent
    ]
})
export class CitationModule { }

