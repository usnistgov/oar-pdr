import { Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  constructor(private toastr: ToastrService) { 

  }

  showSuccess(message, title){
  	this.toastr.success(message, title, {
      positionClass: 'toast-top-right' 
   })
  }

  showSuccessWithTimeout(message, title, timespan){
    this.toastr.info(message, title ,{
      timeOut : timespan,
      positionClass: 'toast-top-right'
    })
  }

  showHTMLMessage(message, title){
    this.toastr.success(message, title, {
      enableHtml : true,
      positionClass: 'toast-top-right'
    })
  }

  showError(message, title){
  	this.toastr.error(message, title, {
      positionClass: 'toast-top-right' 
   })
  }
}