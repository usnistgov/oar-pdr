import { Routes, RouterModule } from '@angular/router';
import { DatacartComponent } from './datacart.component';
import {CanDeactivateGuard} from '../can-deactivate/can-deactivate.guard';

export const DatacartRoutes: Routes = [

  {
    path: 'datacart',
    children: [
        {   path: ':ediid',             
            component: DatacartComponent,
            canDeactivate: [CanDeactivateGuard]   },
        {   path: 'ark:/88434/:ediid',  
            component: DatacartComponent,
            canDeactivate: [CanDeactivateGuard]   }
    ]
  }
];
