import { NgModule } from '@angular/core';
import { SharedService } from './shared/shared/index';
// import { MockSearchService } from './shared/search-service/search-service.service.mock';

@NgModule({
  providers: [
    { provide: SharedService, useClass: SharedService }
  ]
})
export class MockModule {

}