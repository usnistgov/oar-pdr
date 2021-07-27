import { Routes, RouterModule } from '@angular/router';
import { DatacartComponent } from './datacart.component';
import { LeaveWhileDownloadingGuard } from './leave.guard';

export const DatacartRoutes: Routes = [

  {
    path: 'datacart',
    children: [
        {   path: ':cartname',             
            component: DatacartComponent,
            canDeactivate: [LeaveWhileDownloadingGuard]   },
        {   path: 'ark:/:naan/:cartname',  
            component: DatacartComponent,
            canDeactivate: [LeaveWhileDownloadingGuard]   }
    ]
  }
];
