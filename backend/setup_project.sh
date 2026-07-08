#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CareerCompass Kenya — one-shot setup script
# Run from: CareerCompass/backend/
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "── 1. Virtual environment ──────────────────────────────────────────────"
python3 -m venv venv
source venv/bin/activate

echo "── 2. Dependencies ─────────────────────────────────────────────────────"
pip install -r ../requirements.txt

echo "── 3. Environment file ─────────────────────────────────────────────────"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created .env — EDIT IT NOW before continuing."
  echo "  At minimum set: DB_NAME, DB_USER, DB_PASSWORD, DJANGO_SECRET_KEY"
  exit 1
fi

echo "── 4. Database migrations ───────────────────────────────────────────────"
python manage.py migrate

echo "── 5. Seed data ────────────────────────────────────────────────────────"
python manage.py load_mbti_data
python manage.py populate_careers
python manage.py populate_career_subjects
python manage.py populate_learning_styles
python manage.py populate_resources

echo "── 6. Static files ─────────────────────────────────────────────────────"
python manage.py collectstatic --noinput

echo "── 7. Create superuser (admin) ─────────────────────────────────────────"
python manage.py createsuperuser

echo ""
echo "Done. Start the dev server with:"
echo "  source venv/bin/activate"
echo "  cd CareerCompass/backend"
echo "  python manage.py runserver"
