import { Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  constructor(private toastr: ToastrService) { }

  showSuccess(message, title){
  	this.toastr.success(message, title, {
      positionClass: 'toast-bottom-left' 
   })
  }

  showSuccessWithTimeout(message, title, timespan){
    this.toastr.info(message, title ,{
      timeOut : timespan,
      positionClass: 'toast-bottom-left'
    })
  }

  showHTMLMessage(message, title){
    this.toastr.success(message, title, {
      enableHtml : true,
      positionClass: 'toast-bottom-left'
    })
  }
}