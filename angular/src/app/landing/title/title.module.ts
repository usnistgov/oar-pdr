import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { TitleComponent } from './title.component';

/**
 * module that provide support for rendering and editing a resource's title
 */
@NgModule({
    imports: [
        CommonModule
    ],
    declarations: [
        TitleComponent
    ],
    providers: [
    ],
    exports: [
        TitleComponent
    ]
})
export class TitleModule { }

export {
    TitleComponent
};

    
