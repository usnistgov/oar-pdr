import { Component, OnInit} from '@angular/core';
import {MessageService} from 'primeng/api';

import { ActivatedRoute, Router } from '@angular/router';
import { ConfigurationService } from '../services/config.service';
import { RPAService } from '../services/rpa.service';
import { Record } from '../models/record.model';

@Component({
    selector:    'rpa-sme',
    templateUrl: './rpa-sme.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [MessageService, ConfigurationService, RPAService]
  })
export class RPASMEComponent implements OnInit {

    recordId: string;
    status: string;
    record: Record;
    loaded: boolean = false;

    constructor(private route: ActivatedRoute, private router: Router, private rpaService: RPAService, private messageService: MessageService) {     }

    ngOnInit(): void {
        this.status = "pending";
        this.route.queryParams.subscribe(params => {
            this.recordId = params['id'];
            this.rpaService.getRecord(this.recordId).subscribe(data => {
                this.record = data.record;
                this.status = this.record.userInfo.approvalStatus;
                this.loaded = true;
                console.log(this.record)
            });
        });
    }

    onApprove(): void {
        this.rpaService.approveRequest(this.recordId).subscribe(data => {
            console.log("Approved!\n", data)
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'This request was approved sussfully!' });
            this.router.navigate(['/rpa-sme-approved']);
        });
    }

    onDecline(): void {
        this.rpaService.approveRequest(this.recordId).subscribe(data => {
            console.log("Declined!\n", data)
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'This request was declined sussfully!' });
        });
    }



}