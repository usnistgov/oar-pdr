import { TestBed, inject } from '@angular/core/testing';

import { GoogleAnalyticsService } from './google-analytics.service';
import { RouterModule } from '@angular/router';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';

describe('GoogleAnalyticsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterModule, RouterTestingModule],
      providers: [GoogleAnalyticsService]
    });
  });

  it('should be created', () => {
    const service: GoogleAnalyticsService = TestBed.get(GoogleAnalyticsService);

    expect(service).toBeTruthy();
  });
});
