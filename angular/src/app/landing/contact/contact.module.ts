import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ToolbarModule } from 'primeng/toolbar';
import { ToastrModule } from 'ngx-toastr';

import { CollapseModule } from '../collapseDirective/collapse.module';
import { ContactComponent } from './contact.component';
import { ContactPopupComponent } from './contact-popup/contact-popup.component';
import { ContactService } from './contact.service';
import { ButtonModule } from 'primeng/button';

/**
 * module that provide support for rendering and managing a resource's 
 * contact information
 */
@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ToolbarModule,
        CollapseModule,
        ButtonModule,
        ToastrModule.forRoot()
    ],
    declarations: [
        ContactComponent, ContactPopupComponent
    ],
    providers: [
        ContactService
    ],
    exports: [
        ContactComponent, ContactPopupComponent
    ]
})
export class ContactModule { }

export {
    ContactComponent, ContactPopupComponent, ContactService
};

    
