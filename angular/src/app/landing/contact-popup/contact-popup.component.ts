import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { CommonVarService } from '../../shared/common-var';

@Component({
  selector: 'app-contact-popup',
  templateUrl: './contact-popup.component.html',
  styleUrls: ['./contact-popup.component.css']
})
export class ContactPopupComponent implements OnInit {

  @Input() inputValue: any;
  @Input() field: string;
  @Input() title?: string;
  @Output() returnValue: EventEmitter<any> = new EventEmitter();

  tempContactPoint: any;
  tempAddress: string;

  constructor(public activeModal: NgbActiveModal,
              private commonVarService: CommonVarService
    ) { }

  ngOnInit() {
    if (this.inputValue != null && this.inputValue != undefined) {
      this.tempContactPoint = this.commonVarService.deepCopy(this.inputValue['contactPoint']);
    } else {
      this.tempContactPoint = this.commonVarService.getBlankField('contactPoint');
    }

    // strip off "mailto:"
    this.tempContactPoint.hasEmail = this.tempContactPoint.hasEmail.split(":")[1];
    let i: number;
    // Putting address lines together
    if (this.tempContactPoint.address) {
      this.tempAddress = this.tempContactPoint.address[0];
      for (i = 1; i < this.tempContactPoint.address.length; i++) {
        this.tempAddress = this.tempAddress + '\r\n' + this.tempContactPoint.address[i];
      }
    }

    let textArea = document.getElementById("address");
    if(this.tempContactPoint.address != undefined && this.tempContactPoint.address != null)
      textArea.style.height = (this.tempContactPoint.address.length * 30).toString() + 'px';;
  }

  /*
  *   Textarea auto grow
  */
  autogrow(e) {
    let textArea = document.getElementById("address");

    e.target.style.overflow = 'hidden';
    e.target.style.height = '0px';
    e.target.style.height = textArea.scrollHeight + 'px';
  }

  /* 
  *   Save contact info when click on save button in pop up dialog
  */
  saveContactInfo() {
    // Add "mailto:" back
    if (!this.commonVarService.emptyString(this.tempContactPoint.hasEmail)) {
      if (this.tempContactPoint.hasEmail.split(":")[0] != "mailto")
        this.tempContactPoint.hasEmail = "mailto:" + this.tempContactPoint.hasEmail;
    }

    //Handle address
    if(this.tempAddress != undefined && this.tempAddress != null)
      this.tempContactPoint.address = this.tempAddress.split('\n');
    
    // Send update to backend here...

    this.returnValue.emit({"contactPoint": this.tempContactPoint});
    this.activeModal.close('Close click')
  }
}
