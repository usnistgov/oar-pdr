import { TestBed } from '@angular/core/testing';

import { NotificationService } from './notification.service';
import { ToastrModule } from 'ngx-toastr';

describe('NotificationService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [ToastrModule.forRoot()],
  }));

  it('should be created', () => {
    const service: NotificationService = TestBed.get(NotificationService);
    expect(service).toBeTruthy();
  });
});
