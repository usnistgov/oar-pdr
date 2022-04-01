import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultlistComponent } from './resultlist.component';
import { ButtonModule } from 'primeng/button';
import { FormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';

@NgModule({
  declarations: [ResultlistComponent],
  imports: [
    CommonModule, ButtonModule, FormsModule, DropdownModule
  ],
  exports: [
    ResultlistComponent
  ]
})
export class ResultlistModule { }
