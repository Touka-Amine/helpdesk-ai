import { Injectable, signal } from '@angular/core';

const STORAGE_KEY = 'theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  isDark = signal(this.readInitial());

  constructor() {
    this.apply(this.isDark());
  }

  toggle(): void {
    this.set(!this.isDark());
  }

  set(dark: boolean): void {
    this.isDark.set(dark);
    this.apply(dark);
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light');
  }

  private apply(dark: boolean): void {
    document.documentElement.classList.toggle('dark', dark);
  }

  private readInitial(): boolean {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored === 'dark';
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
  }
}
