import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultlistComponent } from './resultlist.component';
import { ButtonModule } from 'primeng/button';
import { PaginationModule } from '../pagination/pagination.module';
import { FormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';

@NgModule({
  declarations: [ResultlistComponent],
  imports: [
    CommonModule, ButtonModule, PaginationModule, FormsModule, DropdownModule
  ],
  exports: [
    ResultlistComponent
  ]
})
export class ResultlistModule { }
