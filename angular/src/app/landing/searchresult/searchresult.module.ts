import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SearchresultComponent } from './searchresult.component';
import { FiltersModule } from '../filters/filters.module';
import { ResultlistModule } from '../resultlist/resultlist.module';
import { TreeModule } from 'primeng/tree';
import { PanelMenuModule } from 'primeng/panelmenu';
import { MessagesModule } from 'primeng/messages';
import { MessageModule } from 'primeng/message';
import { DialogModule } from 'primeng/dialog';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { CheckboxModule } from 'primeng/checkbox';
import { TooltipModule } from 'primeng/tooltip';

@NgModule({
  declarations: [SearchresultComponent],
  imports: [
    CommonModule, FiltersModule, ResultlistModule,
    TreeModule, 
    DialogModule, 
    InputTextModule, 
    PanelMenuModule, 
    OverlayPanelModule, 
    CheckboxModule, 
    TooltipModule,
    MessagesModule,
    MessageModule,
    InputTextareaModule,
    ProgressSpinnerModule,
    MultiSelectModule
  ],
  exports: [
    SearchresultComponent
  ]
})
export class SearchresultModule { }
