import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ToolbarModule } from 'primeng/toolbar';
import { ToastrModule } from 'ngx-toastr';

import { DirectivesModule } from '../../directives/directives.module';
import { DescriptionComponent } from './description.component';
import { DescriptionPopupComponent } from './description-popup/description-popup.component';

/**
 * module that provides support for rendering and managing a resource's text description 
 */
@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ToolbarModule,
        DirectivesModule,
        ToastrModule.forRoot()
    ],
    declarations: [
        DescriptionComponent, DescriptionPopupComponent
    ],
    providers: [
    ],
    exports: [
        DescriptionComponent, DescriptionPopupComponent
    ]
})
export class DescriptionModule { }

export {
    DescriptionComponent, DescriptionPopupComponent
};

    
