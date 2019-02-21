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
  }

  close(){
    this.cartService.clearTheCart();
    this.cartService.setCurrentCart('cart');
    this.cartService.initCart();
    this.cartService.getAllCartEntities();
    this.cartService.setCartLength(this.cartService.cartSize);
    this.modalReference.close();
    this.commonVarService.setForceLandingPageInit(true);
  }
}