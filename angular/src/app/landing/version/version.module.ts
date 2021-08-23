import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { CollapseModule } from '../collapseDirective/collapse.module';
import { VersionComponent } from './version.component';

/**
 * module that provide support for rendering resource's version information
 */
@NgModule({
    imports: [
        CommonModule,
        CollapseModule
    ],
    declarations: [
        VersionComponent
    ],
    providers: [ ],
    exports: [
        VersionComponent
    ]
})
export class VersionModule { }

export {
    VersionComponent
};

    
