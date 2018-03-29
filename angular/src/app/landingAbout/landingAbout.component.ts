import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormBuilder, FormGroup } from '@angular/forms';

import { Todo } from '../to-do/to-do';
import { TodoService } from '../to-do/to-do.service';



@Component({
  selector: 'landing-to-do',
  templateUrl: './landingAbout.component.html',
  styleUrls: ['./landingAbout.component.css']
})
export class LandingAboutComponent implements OnInit {
  formGroup: FormGroup;
  todos: Todo[];

  headerText: string;

  constructor(private _todoService: TodoService, private _formBuilder: FormBuilder) {
    
  }

  ngOnInit() {
    //this.getTodos();
  }

  getTodos() {
    //this.todos = this._todoService.getTodosFromData();
  }

  
}
