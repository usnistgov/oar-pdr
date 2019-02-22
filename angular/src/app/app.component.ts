import { Component, AfterViewInit, OnInit } from '@angular/core';
import { CommonVarService } from './shared/common-var';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements AfterViewInit, OnInit {
  constructor(private commonVarService: CommonVarService) {
  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {
  }

  ngAfterViewInit() {
    setTimeout(() => {
      this.commonVarService.watchContentReady().subscribe(
        value => {
          let element: HTMLElement = document.getElementById('loadspinner') as HTMLElement;
          element.hidden = value;
        }
      );
    });
  }
}
