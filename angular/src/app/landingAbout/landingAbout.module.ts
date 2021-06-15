import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { LandingAboutComponent } from './landingAbout.component';

/**
 * module that provides the PDR About Page
 */
@NgModule({
    imports: [
        CommonModule
    ],
    declarations: [
        LandingAboutComponent
    ],
    providers: [ ],
    exports: [
        LandingAboutComponent
    ]
})
export class LandingAboutModule { }

export {
    LandingAboutComponent
};
