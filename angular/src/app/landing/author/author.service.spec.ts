import { TestBed } from '@angular/core/testing';

import { AuthorService } from './author.service';

describe('AuthorService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: AuthorService = TestBed.get(AuthorService);
    expect(service).toBeTruthy();
  });
});
