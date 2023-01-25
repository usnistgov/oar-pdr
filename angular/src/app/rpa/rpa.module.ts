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
import { RPARequestFormComponent } from "./components/request-form.component";
import { RPASMEComponent } from "./components/rpa-sme.component";
import {ProgressSpinnerModule} from 'primeng/progressspinner';
import {OverlayPanelModule} from 'primeng/overlaypanel';

@NgModule({
    imports: [CommonModule, ReactiveFormsModule, PanelModule, MessagesModule, MessageModule, FormsModule, DropdownModule, CardModule, ChipModule, ButtonModule, ProgressSpinnerModule, OverlayPanelModule],
    declarations: [RPARequestFormComponent, RPASMEComponent],
    exports: []
})
export class RPAModule {

}