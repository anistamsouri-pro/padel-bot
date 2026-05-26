# 🎾 Padel Bot 

Agent automatique de réservation de créneaux padel sur ballejaune.com, déployé sur GitHub Actions + Pages.

## Architecture

- **Frontend** : `index.html`, page mobile-friendly servie par **GitHub Pages**
- **Backend** : workflow **GitHub Actions** qui exécute le bot Playwright dans un container Ubuntu
- **Trigger** : la page web déclenche le workflow via l'API GitHub, en utilisant un Personal Access Token (PAT)

## Utilisation

1. Ouvrir la page : `https://anistamsouri-pro.github.io/padel-bot/`
2. Configurer une seule fois ton PAT GitHub (⚙️ en haut à droite)
3. Choisir jour / heure / terrains → cliquer « Lancer le bot »
4. Le bot tourne sur GitHub, la réservation est faite à la milliseconde près

## Règles ballejaune Les Pyramides

- **Semaine** (Lun–Ven) : ouverture J-2 à 17h00
- **Week-end** (Sam–Dim) : ouverture J-1 à 19h30

## Limite technique

Un workflow Actions a un timeout de 6h. Donc déclencher le bot **au plus 5h30 avant l'ouverture du créneau visé**.

## Local dev (optionnel)

Si tu veux tester en local sur ton Mac sans passer par GitHub :

```bash
cd ~/padel-agent
source .venv/bin/activate
python app.py
# Ouvre http://127.0.0.1:8000
```

## Secrets GitHub requis

À configurer dans `Settings → Secrets and variables → Actions` :

- `BJ_EMAIL` — email du compte ballejaune
- `BJ_PASSWORD` — mot de passe ballejaune
- `CLUB_URL` — `https://ballejaune.com/club/les-pyramides`
