import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';

import { ModalComponent } from './modal.component';
import { AppShellNoRenderDirective } from './app-shell-no-render.directive';
import { AppShellRenderDirective } from './app-shell-render.directive';
import { ContenteditableModel } from './contenteditable-model.directive';

/**
 * module that provides general purpose directives
 */
@NgModule({
    imports: [
        CommonModule
    ],
    declarations: [
        ModalComponent, AppShellNoRenderDirective, AppShellRenderDirective, ContenteditableModel
    ],
    exports: [
        ModalComponent, AppShellNoRenderDirective, AppShellRenderDirective, ContenteditableModel
    ]
})
export class DirectivesModule { }

export {
    ModalComponent, AppShellNoRenderDirective, AppShellRenderDirective, ContenteditableModel
};

    
