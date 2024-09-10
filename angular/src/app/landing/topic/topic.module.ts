import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TreeTableModule } from 'primeng/treetable';
import { ToolbarModule } from 'primeng/toolbar';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { ToastrModule } from 'ngx-toastr';

import { TopicComponent } from './topic.component';
import { SearchTopicsComponent } from './topic-popup/search-topics.component';
import { ButtonModule } from 'primeng/button';
import { ChipsModule } from 'primeng/chips';
import { ChipModule } from "primeng/chip";
/**
 * module that provide support for rendering and managing a resource's list of 
 * applicable research topics
 */
@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ToolbarModule,
        TreeTableModule,
        OverlayPanelModule,
        ButtonModule,
        ChipsModule,
        ChipModule,
        ToastrModule.forRoot()
    ],
    declarations: [
        TopicComponent, SearchTopicsComponent
    ],
    providers: [
    ],
    exports: [
        TopicComponent, SearchTopicsComponent
    ]
})
export class TopicModule { }

export {
    TopicComponent, SearchTopicsComponent
};

    
