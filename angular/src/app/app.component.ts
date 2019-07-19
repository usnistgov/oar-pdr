import { Component, AfterViewInit, OnInit } from '@angular/core';
import { CommonVarService } from './shared/common-var';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'PDR Resource Landing Page';
}

