import { TestBed } from '@angular/core/testing';

import { EditControlService } from './edit-control.service';

describe('EditControlService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: EditControlService = TestBed.get(EditControlService);
    expect(service).toBeTruthy();
  });
});
