import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

//import { AboutComponent }   from './about/About.component';
import { LandingAboutComponent } from './landingAbout/landingAbout.component';
import { LandingComponent } from './landing/landing.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { SearchResolve } from './landing/search-service.resolve';
import { ErrorComponent, UserErrorComponent } from './landing/error.component';
import { DatacartComponent} from './datacart/datacart.component';

const routes: Routes = [
  { path: '', redirectTo: '/about', pathMatch: 'full' },
  { path: 'about',  children: [
    {
      path: '',
     component: LandingAboutComponent
    } ] 
  },
 {path: 'od/id/:id',
   children: [
   {
     path: '',
     component: LandingComponent,
     resolve: {
       searchService: SearchResolve
     }
   }
 ]}, {
  path: 'od/id/ark:/88434/:id',
  children: [
    {
      path: '',
      component: LandingComponent,
      resolve: {
        searchService: SearchResolve
      }
    }
  ]
},{
  path: 'od/id',
  children: [
    {
      path: '',
      component: NoidComponent,
      
    }
  ]
}
,{
  path: 'od/id/nerdm',
  children: [
    {
      path: '',
      component: NerdmComponent
    }
  ]
},{
  path: 'datacart',
  children: [
      {
        path: '',
        component: DatacartComponent
      }
  ]
},{
  path: 'od/id/error/:id',
  children: [
    {
      path: '',
      component: ErrorComponent
    }
  ]
}
,{
  path: 'od/id/usererror/:id',
  children: [
    {
      path: '',
      component: UserErrorComponent
    }
  ]
}
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ],
  providers: [ SearchResolve ]
})
export class AppRoutingModule {}
