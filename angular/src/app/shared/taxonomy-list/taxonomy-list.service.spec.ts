import { TestBed } from '@angular/core/testing';

import { TaxonomyListService } from './taxonomy-list.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { RouterModule } from '@angular/router';
import { Location } from '@angular/common';

describe('TaxonomyListService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [HttpClientTestingModule, RouterModule, RouterTestingModule],
    providers: [Location]
  }));

  it('should be created', () => {
    const service: TaxonomyListService = TestBed.get(TaxonomyListService);
    expect(service).toBeTruthy();
  });
});
