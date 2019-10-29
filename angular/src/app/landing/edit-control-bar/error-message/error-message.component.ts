import { Component, OnInit, Input } from '@angular/core';
import { ErrorHandlingService } from '../../../shared/error-handling-service/error-handling.service';
import { errMessage } from '../../../shared/error-handling-service/error-handling.service';

@Component({
    selector: 'error-message',
    templateUrl: './error-message.component.html',
    styleUrls: ['../../landing.component.css']
})
export class ErrorMessageComponent implements OnInit {
    errMessage: errMessage;
    displayError: boolean = false;
    action: string = "";

    constructor(private errorHandlingService: ErrorHandlingService) {
        this.errorHandlingService.watchErrMessage().subscribe(value => {
            this.errMessage = value;
        });
    }

    ngOnInit() {
    }

}
