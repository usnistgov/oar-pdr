import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'pdr-done',
  templateUrl: './done.component.html',
  styleUrls: ['./done.component.css']
})
export class DoneComponent implements OnInit {
    @Input() message: string;

    constructor() { }

    ngOnInit() {
    }

}
