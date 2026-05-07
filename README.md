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
```

---

# Estructura del Google Sheet

| columna | descripció |
|---|---|
| nom | Nom de la convocatòria |
| url | URL principal de la convocatòria |
| paraules_clau | Keywords necessàries per detectar convocatòria |
| mes_habitual | Mes habitual d’obertura |
| estat | Estat actual (`PUBLICADA`, `NO TROBADA`, `ERROR`) |
| activa | `Si` / `No` |
| ultima_revisio | Última execució |
| enllac_bases | Enllaç detectat |
| observacions | Resultat de detecció |
| paraules_excloses | Keywords que invaliden detecció |
| pdfs_detectats | PDFs detectats a la web |

---

# Tecnologies utilitzades

- Python
- BeautifulSoup4
- Requests
- gspread
- Google Sheets API
- GitHub Actions
- Telegram Bot API

---

# Configuració

## 1. Crear Google Service Account

Cal:
- activar Google Sheets API
- activar Google Drive API
- crear una Service Account
- descarregar el JSON
- compartir el Google Sheet amb l’email de la Service Account

---

## 2. GitHub Secrets

Afegir aquests secrets:

```text
TELEGRAM_TOKEN
CHAT_ID
GOOGLE_CREDENTIALS_JSON
```

---

# GitHub Actions

Workflow programat:

```yaml
on:
  schedule:
    - cron: "0 8 1,15 * *"
  workflow_dispatch:
```

Execució:
- dies 1 i 15 de cada mes
- també manual via GitHub Actions

---

# Detecció de convocatòries

El sistema marca una convocatòria com a activa quan:

- detecta almenys 2 keywords
- no detecta paraules excloses
- o detecta PDFs nous

També afegeix automàticament:
- any actual (`2026`, `2027`, etc.)

---

# Exemple de paraules clau

```text
fero, young investigator, translational cancer research
```

## Exemple de paraules excloses

```text
closed, convocatoria cerrada, finalizado, expired
```

---

# Exemple d’alerta Telegram

```text
📢 CONVOCATÒRIA DETECTADA

Nom: FERO Young Investigator Award
Enllaç: https://...

PDFs nous detectats: 1
```

---

# Estructura del repositori

```text
monitoratge-convocatories/
├── monitoratge.py
├── requirements.txt
└── .github/
    └── workflows/
        └── monitoratge.yml
```

---

# Possibles millores futures

- Detecció de nous enllaços
- Comparació de versions de pàgina
- Hash SHA256 del contingut
- Integració amb IA per validar convocatòries
- Dashboard visual
- Suport per PDFs OCR
- Exportació automàtica de resultats

---

# Llicència

Projecte d’ús personal i acadèmic.
