import { TestBed } from '@angular/core/testing';

import { SearchfieldsListService } from './searchfields-list.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { RouterModule } from '@angular/router';
import { Location } from '@angular/common';

describe('SearchfieldsListService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [HttpClientTestingModule, RouterModule, RouterTestingModule],
    providers: [Location]
  }));

  it('should be created', () => {
    const service: SearchfieldsListService = TestBed.get(SearchfieldsListService);
    expect(service).toBeTruthy();
  });
});
