import { NgModule } from "@angular/core";
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { PanelModule } from 'primeng/panel';

import { MessagesModule } from 'primeng/messages';
import { MessageModule } from 'primeng/message';
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { ChipModule } from 'primeng/chip';
import { ButtonModule } from "primeng/button";
import { RPDRequestFormComponent } from "./components/request-form.component";
import { TermsComponent } from "./components/terms.component";
import { AgreementComponent } from "./components/agreement.component";
import { RPDSMEComponent } from "./components/rpd-sme.component";

@NgModule({
    imports: [CommonModule, ReactiveFormsModule, PanelModule, MessagesModule, MessageModule, DropdownModule, FormsModule, CardModule, ChipModule, ButtonModule],
    declarations: [RPDRequestFormComponent, TermsComponent, AgreementComponent, RPDSMEComponent],
    exports: []
})
export class RPDModule {

}