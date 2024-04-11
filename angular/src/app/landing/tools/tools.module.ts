import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { MenuModule } from 'primeng/menu';
import { ToolMenuComponent } from './toolmenu.component';
import { MenuComponent } from './menu/menu.component';
import { MetricsinfoModule } from '../metricsinfo/metricsinfo.module';

/**
 * A module providing tools for interacting with the landing page's record metadata.  
 *
 * This includes the right-hand menu for navigating the record, displaying citation information, 
 * and searching for related records.
 */
@NgModule({
    imports: [
        CommonModule,
        MenuModule,
        MetricsinfoModule
    ],
    declarations: [
        ToolMenuComponent,
        MenuComponent
    ],
    exports: [
        ToolMenuComponent,
        MenuComponent
    ]
})
export class ToolsModule { }

