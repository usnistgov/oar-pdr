import { Routes, RouterModule } from '@angular/router';
import { DatacartComponent } from './datacart.component';
import {CanDeactivateGuard} from '../can-deactivate/can-deactivate.guard';

export const DatacartRoutes: Routes = [

  {
    path: 'datacart/:ediid',
    component: DatacartComponent,
    canDeactivate: [CanDeactivateGuard]
  }
];
