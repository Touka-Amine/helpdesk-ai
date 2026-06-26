import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router'; // <-- 1. On importe le routeur

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet], // <-- 2. On déclare RouterOutlet (et on efface TestApi)
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'frontend';
}