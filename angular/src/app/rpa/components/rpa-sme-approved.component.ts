import { Component, OnInit } from "@angular/core";
import {Message} from 'primeng//api';
import {MessageService} from 'primeng/api';

@Component({
    selector:    'rpa-sme-approved',
    templateUrl: './rpa-sme-approved.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [MessageService]
  })
export class RPASMEApprovedComponent implements OnInit {

    msgs: Message[];

    constructor(private messageService: MessageService) {}

    ngOnInit() {
        this.msgs = [
            {severity:'success', summary:'Success', detail:'The request has been approved successfully. Thanks for your assistance!'}
        ]; 
    }
}