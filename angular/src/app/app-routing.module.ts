import { NgModule }             from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

//import { AboutComponent }   from './about/About.component';
import { ToDoComponent } from './to-do/to-do.component';
import { LandingAboutComponent } from './landingabout/landingabout.component';
import { LandingComponent } from './landing/landing.component';
import { NoidComponent } from './landing/noid.component';
import { NerdmComponent } from './landing/nerdm.component';
import { SearchResolve } from './landing/search-service.resolve';

const routes: Routes = [
  { path: '', redirectTo: '/aboutlanding', pathMatch: 'full' },
  { path: 'aboutlanding', component: LandingAboutComponent },
 { path: 'todo', component: ToDoComponent },
 {path: 'id/:id',
   children: [
   {
     path: '',
     component: LandingComponent,
     resolve: {
       searchService: SearchResolve
     }
   }
 ]}, {
  path: 'id/ark:/88434/:id',
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
  path: 'id',
  children: [
    {
      path: '',
      component: NoidComponent,
      
    }
  ]
}
,{
  path: 'nerdm',
  children: [
    {
      path: '',
      component: NerdmComponent
    }
  ]
}
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ],
  providers: [ SearchResolve]
})
export class AppRoutingModule {}
