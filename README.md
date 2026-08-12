# Drive2School — version finale prête pour Supabase + Render

## 1. Installation locale

PowerShell :

```powershell
cd C:\Dev\Drive2School
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Puis ouvrir :

http://127.0.0.1:8000/

## 2. Fonctionnalités déjà préparées

- Accueil avec hero
- Inscription / connexion / déconnexion
- Liste et recherche des trajets
- Détail d'un trajet
- Création d'un trajet
- Modification d'un trajet
- Suppression d'un trajet
- Gestion des places
- Réservation
- Annulation d'une réservation
- Tableau de bord
- Administration Django
- PostgreSQL via DATABASE_URL
- WhiteNoise pour les fichiers statiques
- Configuration compatible Render

## 3. Développement local

Sans DATABASE_URL, Django utilise automatiquement SQLite.

Avec DATABASE_URL, Django utilise PostgreSQL.

Ne mettez jamais de secret dans Git.

## 4. Supabase

Créer une base PostgreSQL Supabase et récupérer l'URL de connexion PostgreSQL.

Dans Render, créer :

- DATABASE_URL
- SECRET_KEY
- DEBUG=False
- ALLOWED_HOSTS=nom-du-service.onrender.com
- CSRF_TRUSTED_ORIGINS=https://nom-du-service.onrender.com

## 5. Render

Build Command :

```bash
./build.sh
```

Start Command :

```bash
gunicorn config.wsgi:application
```

Le fichier build.sh effectue collectstatic et migrate.

## 6. Git

```powershell
git init
git add .
git commit -m "Drive2School final"
```

Puis pousser vers GitHub.

## 7. Attention

Le fichier `.env` ne doit jamais être envoyé à GitHub.

Le fichier `.env.example` est volontairement sans secrets.
