import { NgModule } from '@angular/core';
import { CommonVarService } from './shared/common-var/index';
// import { MockSearchService } from './shared/search-service/search-service.service.mock';

@NgModule({
  providers: [
    { provide: CommonVarService, useClass: CommonVarService }
  ]
})
export class MockModule {

}