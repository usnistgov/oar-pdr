import { TestBed } from '@angular/core/testing';

import { CustomizationServiceService } from './customization-service.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonVarService } from '../common-var/common-var.service';
import { RouterTestingModule } from '@angular/router/testing';

describe('CustomizationServiceService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [HttpClientTestingModule, RouterTestingModule],
    providers: [
      {provide: CommonVarService}
    ]
  }));

  it('should be created', () => {
    const service: CustomizationServiceService = TestBed.get(CustomizationServiceService);
    expect(service).toBeTruthy();
  });
});
