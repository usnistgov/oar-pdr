import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-description-popup',
  templateUrl: './description-popup.component.html',
  styleUrls: ['./description-popup.component.css']
})
export class DescriptionPopupComponent implements OnInit {
  @Input() tempDecription: string;
  @Input() title: string;
  @Output() returnDescription: EventEmitter<any> = new EventEmitter();

  constructor(public activeModal: NgbActiveModal) { }

  ngOnInit() {
    let textArea = document.getElementById("address");
  }

  saveDescription() {
    this.returnDescription.emit(this.tempDecription);
    window.scroll(0, 0);
    this.activeModal.close('Close click');
  }

  cancelChange(){
    window.scroll(0, 0);
    this.activeModal.close('Close click');
  }
}
