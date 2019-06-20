import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-description-popup',
  templateUrl: './description-popup.component.html',
  styleUrls: ['./description-popup.component.css']
})
export class DescriptionPopupComponent implements OnInit {
  @Input() tempDecription: string;
  @Output() returnDescription: EventEmitter<any> = new EventEmitter();

  constructor(public activeModal: NgbActiveModal) { }

  ngOnInit() {
    console.log('tempDecription', this.tempDecription);
  }

  saveDescription(){
    this.returnDescription.emit(this.tempDecription);
    this.activeModal.close('Close click')
  }
}
