import { Component, OnInit } from '@angular/core';
import { NgbModal, ModalDismissReasons, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { CommonVarService } from '../../shared/common-var';
import { DatacartComponent } from '../../datacart/datacart.component';
import { ViewChild, ElementRef } from '@angular/core';
import { DownloadService } from '../../shared/download-service/download-service.service';
import { CartService } from '../../datacart/cart.service';

@Component({
  selector: 'ngbd-modal-download-manager',
  templateUrl: './downloadmodal.component.html',
  providers: [NgbActiveModal]
})
export class NgbdModalDownloadManager implements OnInit {
  closeResult: string;
  modalReference: any;

  @ViewChild('content') contentRef: ElementRef;

  constructor(private modalService: NgbModal,
    private cartService: CartService,
    public modal: NgbModal,
    public activeModal: NgbActiveModal,
    private downloadService: DownloadService,
    private commonVarService: CommonVarService) {
    this.commonVarService.watchShowDatacart().subscribe(
      value => {
        if (value) {
          this.downloadService.setFireDownloadAllFlag(true);
          this.downloadService.setIsPopupFlag(true);
          this.open();
        }
      }
    );
  }

  ngOnInit() {
  }

  open() {
    this.modalReference = this.modalService.open(
      this.contentRef, 
      { windowClass: "myCustomModalClass",
        beforeDismiss: () => {
          return false;
        }
      }
    );
    // this.modalReference.result.then((result) => {
    //   this.closeResult = `Closed with: ${result}`;
    // }, (reason) => {
    //   this.closeResult = `Dismissed ${this.getDismissReason(reason)}`;
    // });
  }

  close(){
    this.cartService.setCurrentCart('cart');
    this.modalReference.close();
  }

  // private getDismissReason(reason: any): string {
  //   if (reason === ModalDismissReasons.ESC) {
  //     return 'by pressing ESC';
  //   } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
  //     return 'backdrop';
  //   } else {
  //     return `with: ${reason}`;
  //   }
  // }
}