import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApprovalQueue } from './approval-queue';

describe('ApprovalQueue', () => {
  let component: ApprovalQueue;
  let fixture: ComponentFixture<ApprovalQueue>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ApprovalQueue],
    }).compileComponents();

    fixture = TestBed.createComponent(ApprovalQueue);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
