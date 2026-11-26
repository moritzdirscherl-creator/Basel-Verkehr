# Reicht's? Basel

Prototyp einer ÖV-App für Basel: Zeigt pro Verbindung, wo die Trams und Busse gerade sind, ob der Anschluss reicht (Ampel), und einen Plan B ab dem Umsteigeort.

- Daten: [transport.opendata.ch](https://transport.opendata.ch) (Fahrplan + Echtzeit-Prognose, kein API-Key)
- Fahrzeugpositionen werden aus Prognose und Fahrplan zwischen den Haltestellen interpoliert (keine GPS-Daten)
- Karte: Leaflet, Kacheln © OpenStreetMap-Mitwirkende © CARTO

Live via GitHub Pages: Settings → Pages → Deploy from a branch → `main` / `(root)`.
