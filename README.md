# Convocatòries Monitoratge

Sistema automàtic de monitoratge de convocatòries de recerca mitjançant Python, Google Sheets, GitHub Actions i Telegram.

---

# Funcionalitats

- Revisió automàtica de webs de convocatòries
- Detecció basada en paraules clau
- Exclusió de falsos positius amb paraules prohibides
- Detecció automàtica de PDFs nous
- Enviament d’alertes a Telegram
- Actualització automàtica d’un Google Sheet
- Execució automàtica amb GitHub Actions
- Activació/desactivació individual de convocatòries
- Afegiment dinàmic de l’any actual com a keyword

---

# Arquitectura

```text
GitHub Actions
      ↓
Python monitoratge.py
      ↓
Google Sheets (backend)
      ↓
Scraping de convocatòries
      ↓
Detecció de novetats
      ↓
Alertes Telegram
