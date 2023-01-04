import { Component, OnInit} from '@angular/core';
import {MessageService} from 'primeng/api';

import { ActivatedRoute } from '@angular/router';
import { ConfigurationService } from '../services/config.service';
import { RPDService } from '../services/rpd.service';
import { Record } from '../models/record.model';

@Component({
    selector:    'rpd-sme',
    templateUrl: './rpd-sme.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [MessageService, ConfigurationService, RPDService]
  })
export class RPDSMEComponent implements OnInit {

    recordId: string;
    status: string;
    record: Record;

    constructor(private route: ActivatedRoute, private rpdService: RPDService) {     }

    ngOnInit(): void {
        this.status = "pending";
        this.route.queryParams.subscribe(params => {
            this.recordId = params['id'];
            if (!params['status']) {
                this.status = "pending";
                this.rpdService.getRecord(this.recordId).subscribe(data => {
                    this.record = data.record;
                    console.log(this.record)
                })
            } else {
                this.status = params['status'];
            }
        });
    }

    onApprove(): void {
        
    }



}