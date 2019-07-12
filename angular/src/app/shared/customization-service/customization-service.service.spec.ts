import { TestBed } from '@angular/core/testing';

import { CustomizationServiceService } from './customization-service.service';

describe('CustomizationServiceService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CustomizationServiceService = TestBed.get(CustomizationServiceService);
    expect(service).toBeTruthy();
  });
});
