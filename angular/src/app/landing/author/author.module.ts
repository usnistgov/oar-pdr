import { NgModule }     from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ToolbarModule } from 'primeng/toolbar';
import { ToastrModule } from 'ngx-toastr';

import { CollapseModule } from '../collapseDirective/collapse.module';
import { SharedModule } from '../../shared/shared.module';
import { AuthorComponent } from './author.component';
import { AuthorPopupComponent } from './author-popup/author-popup.component';
import { AuthorService } from './author.service';
import { ButtonModule } from 'primeng/primeng';

/**
 * module that provide support for rendering and managing a resource's 
 * author list
 */
@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        SharedModule,
        ToolbarModule,
        CollapseModule,
        ButtonModule,
        ToastrModule.forRoot()
    ],
    declarations: [
        AuthorComponent, AuthorPopupComponent
    ],
    providers: [
        AuthorService
    ],
    exports: [
        AuthorComponent, AuthorPopupComponent
    ]
})
export class AuthorModule { }

export {
    AuthorComponent, AuthorPopupComponent, AuthorService
};

    
