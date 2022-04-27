import { NgModule,CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { MetricsComponent } from './metrics.component';
import { HorizontalBarchartComponent } from './horizontal-barchart/horizontal-barchart.component';
import { MetricsService } from '../shared/metrics-service/metrics.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TreeModule } from 'primeng/tree';
import { FieldsetModule } from 'primeng/fieldset';
import { DialogModule } from 'primeng/dialog';
import { OverlayPanelModule } from 'primeng/overlaypanel';

@NgModule({
    declarations: [ 
        MetricsComponent, 
        HorizontalBarchartComponent
    ],
    imports: [
        NgbModule, TreeModule, FieldsetModule, DialogModule, OverlayPanelModule, TreeTableModule, ButtonModule,CommonModule, FormsModule
    ],
    exports: [
        MetricsComponent, HorizontalBarchartComponent
    ],
    providers: [
        MetricsService
    ]
})
export class MetricsModule {

}
