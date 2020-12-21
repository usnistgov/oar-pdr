import { TestBed } from '@angular/core/testing';

import { BundleplanService } from './bundleplan.service';

describe('BundleplanService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: BundleplanService = TestBed.get(BundleplanService);
    expect(service).toBeTruthy();
  });
});
