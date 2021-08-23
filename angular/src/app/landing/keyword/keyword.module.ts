import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ToolbarModule } from 'primeng/toolbar';
import { ToastrModule } from 'ngx-toastr';

import { KeywordComponent } from './keyword.component';

/**
 * module that provide support for rendering and managing a resource's list of 
 * applicable research topics
 */
@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ToolbarModule,
        ToastrModule.forRoot()
    ],
    declarations: [
        KeywordComponent
    ],
    providers: [
    ],
    exports: [
        KeywordComponent
    ]
})
export class KeywordModule { }

export {
    KeywordComponent
};

    
