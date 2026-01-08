# Las 41 — MVP (variante) — Python + Flask-SocketIO

Descripción
- Aplicación web multiplayer para jugar una variante de "Las 41".
- Backend: Python, Flask, Flask-SocketIO (eventlet).
- Frontend: HTML + JS (Socket.IO client).
- Soporta hasta 10 jugadores por sala y bots en servidor.

Reglas por defecto (variante implementada)
- Baraja española 40 cartas (1–7, 10–12).
- Valores: 1–7 -> valor numérico; 10–12 -> 10 puntos.
- Reparto equitativo del mazo entre los jugadores.
- Juego por bazas: cada jugador juega 1 carta por turno; gana la baza la carta de mayor rango.
- Puntuación: suma de valores de las cartas ganadas. Objetivo: 41 puntos.

Requisitos
- Python 3.9+
- Recomendado crear virtualenv

Instalación
1. git clone ...
2. cd las41
3. python -m venv venv
4. source venv/bin/activate (Unix) o venv\Scripts\activate (Windows)
5. pip install -r requirements.txt

Ejecución
- Ejecutar: python app.py
- Abre en el navegador: http://localhost:5000
- Crear sala, unir jugadores (hasta 10), añadir bots si se desea, luego `Start Game`.

Estructura
- app.py — servidor Flask + SocketIO
- game.py — lógica de cartas, jugadores, salas y mecánica básica
- static/index.html — interfaz cliente
- static/client.js — cliente Socket.IO y UI
- requirements.txt

Notas y siguientes pasos posibles
- Mejorar IA de bots (heurísticas y memoria).
- Añadir persistencia (SQLite/Postgres) para salas/estadísticas.
- Añadir autenticación y cuentas de usuario.
- Ajustar reglas a versión exacta de "Las 41" si me das la especificación.