import { TestBed, async } from '@angular/core/testing';

import { AuthService } from './auth.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonVarService } from '../common-var/common-var.service';
import { RouterTestingModule } from '@angular/router/testing';

describe('AuthService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [HttpClientTestingModule, RouterTestingModule],
    providers: [
      {provide: CommonVarService}
    ]
  }));

  it('should be created', async(() => {
    const service: AuthService = TestBed.get(AuthService);
    expect(service).toBeTruthy();
  }));
});
