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

  /**
   * Le choix retenu sur le poste, sombre à défaut.
   *
   * Le mode sombre est celui dans lequel l'application a été dessinée : c'est
   * donc lui qu'on voit à la première visite, sur l'écran de connexion, où la
   * bascule permet de passer au clair avant même de saisir ses identifiants.
   */
  private readInitial(): boolean {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? stored === 'dark' : true;
  }
}
