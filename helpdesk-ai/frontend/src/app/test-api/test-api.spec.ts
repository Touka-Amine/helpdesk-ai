import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing'; // Pour simuler les API
import { TestApiComponent } from './test-api.component';


describe('TestApiComponent', () => {
  let component: TestApiComponent;
  let fixture: ComponentFixture<TestApiComponent>;

  beforeEach(async () => {
    // On configure un mini-environnement Angular juste pour ce test
    await TestBed.configureTestingModule({
      imports: [TestApiComponent, HttpClientTestingModule]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(TestApiComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // Le test réel : "Est-ce que le composant arrive à se créer sans crasher ?"
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});