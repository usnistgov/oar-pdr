import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MetrixComponent } from './metrix.component';

describe('MetrixComponent', () => {
  let component: MetrixComponent;
  let fixture: ComponentFixture<MetrixComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MetrixComponent ],
      imports: [FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MetrixComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
