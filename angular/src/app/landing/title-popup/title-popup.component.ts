import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { CommonVarService } from '../../shared/common-var';

@Component({
  selector: 'app-title-popup',
  templateUrl: './title-popup.component.html',
  styleUrls: ['./title-popup.component.css']
})
export class TitlePopupComponent implements OnInit {
  @Input() inputTitle: any;
  @Output() returnTitle: EventEmitter<any> = new EventEmitter();

  constructor(public activeModal: NgbActiveModal) { }

  ngOnInit() {
  }

  saveTitle(){
    this.returnTitle.emit(this.inputTitle);
    this.activeModal.close('Close click')
  }
}
