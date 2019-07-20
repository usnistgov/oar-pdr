import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RouterModule } from '@angular/router';
import { HeadbarComponent } from "./headbar.component";
import { FootbarComponent } from "./footbar.component";

/**
 * A module that provides components that make up the "frame" of the landing 
 * page--namely, the header and the footer.
 */
@NgModule({
    declarations: [
        HeadbarComponent,
        FootbarComponent
    ],
    imports: [
        CommonModule,       // provides template directives
        RouterModule        // allow use of [routerLink]
    ],
    exports: [ HeadbarComponent, FootbarComponent ]
})
export class FrameModule {

}

