import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultlistComponent } from './resultlist.component';
import { ButtonModule } from 'primeng/button';
import { FormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';
import { ResultitemComponent } from '../resultitem/resultitem.component';

@NgModule({
  declarations: [ResultlistComponent, ResultitemComponent],
  imports: [
    CommonModule, ButtonModule, FormsModule, DropdownModule
  ],
  exports: [
    ResultlistComponent, ResultitemComponent
  ]
})
export class ResultlistModule { }
