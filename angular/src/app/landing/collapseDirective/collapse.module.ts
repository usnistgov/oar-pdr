import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { Collapse } from './collapse.directive';

/**
 * module that provides the collapse, a directive for collapsible content
 */
@NgModule({
    imports: [
        CommonModule
    ],
    declarations: [
        Collapse
    ],
    exports: [
        Collapse
    ]
})
export class CollapseModule { }

export { Collapse };
