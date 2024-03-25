import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TaxonomyComponent } from './taxonomy.component';
import { TreeModule } from 'primeng/tree';
import { PanelMenuModule } from 'primeng/panelmenu';
import { AutoCompleteModule } from 'primeng/autocomplete';
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
import { FormsModule } from '@angular/forms';

@NgModule({
  declarations: [TaxonomyComponent],
  imports: [
    CommonModule,
    TreeModule,
    DialogModule, 
    InputTextModule, 
    PanelMenuModule, 
    OverlayPanelModule, 
    CheckboxModule, 
    TooltipModule,
    AutoCompleteModule,
    MessagesModule,
    MessageModule,
    InputTextareaModule,
    ProgressSpinnerModule,
    MultiSelectModule,
    FormsModule
  ],
  exports: [TaxonomyComponent]
})
export class TaxonomyModule { }
