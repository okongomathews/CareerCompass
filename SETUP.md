# CareerCompass Kenya — Setup Guide

## Quick Start

```bash
# 1. Extract archive (adjust filename/flags to match what you actually have —
#    e.g. `tar -xf careercompass.tar.gz` for a plain tar, `-xzf` if gzipped)
tar -xf careercompass_archive.tar
cd CareerCompass/backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Configure environment
cp ../.env .env
# Edit .env — set DB credentials, optionally OPENAI_API_KEY or HF_API_TOKEN

# 5. Database migrations
python manage.py migrate

# 6. ⚠️  CRITICAL: Fix existing admin users (sets is_staff=True)
python manage.py fix_admin_users

# 7. Load MBTI questions (60 balanced questions, 15 per dimension)
python manage.py load_mbti_data --clear

# 8. Load career data (if not already loaded)
python manage.py populate_extended_data

# 9. Run development server
python manage.py runserver
```

## AI Coach Configuration

The AI coach uses a **3-tier fallback**:

| Tier | Provider | Setup |
|------|----------|-------|
| 1 | OpenAI GPT-4o-mini | Set `OPENAI_API_KEY=sk-...` in `.env` |
| 2 | HuggingFace (flan-t5-large) | Optional: set `HF_API_TOKEN=hf_...` for higher rate limits. Free without token for basic use. Get token at huggingface.co/settings/tokens |
| 3 | Rule-based (Kenya-specific) | Always works, no API key needed |

Even without any API keys, **Tier 3 provides rich, useful responses** covering careers, KCSE, universities, study tips, and Kenyan job market data.

## Bugs Fixed in This Version

### 1. Registration Page Blank
**Root cause:** `register.html` used `{% block content %}` but `base.html` renders `{% block auth_content %}` for unauthenticated users.  
**Fix:** Changed to `{% block auth_content %}` — all auth pages now consistent.

### 2. Admin Dashboard 403 / Redirect Loop  
**Root cause:** `@staff_member_required` checks `is_staff=True`, but the registration form only set `user_type='admin'`, never `is_staff=True`.  
**Fix:** (a) Form `save()` now sets `is_staff=True` for admin role. (b) Custom `@admin_required` decorator accepts **either** `is_staff=True` **or** `user_type='admin'`. (c) `fix_admin_users` command patches existing accounts.

### 3. Assessment Submit Button Never Appears  
**Root cause:** JavaScript `responses{}` object starts empty on page load; the completion check `every(q => responses[q.id])` always failed after a page refresh even when all questions were server-saved.  
**Fix:** Pre-populate `responses[qid] = '__saved__'` for all server-saved question IDs at page load.

### 4. Question Display (HCI Optimisation)  
**Before:** Answer buttons in a vertical list — cognitive overload with 7 choices.  
**After:** 7-point **horizontal Likert scale** — the gold standard in psychometric research for balanced questionnaires:
- Green shading = agree end (A-pole)
- Red shading = disagree end (B-pole)  
- Grey = neutral midpoint
- Segmented progress bar shows per-dimension progress (E/I, S/N, T/F, J/P)
- Keyboard shortcuts: 1-7 to answer, ←/→ to navigate between questions

### 5. AI Coach Non-Functional  
**Fix:** Complete rewrite with 3-tier architecture (OpenAI → HuggingFace → rule-based).

## User Roles

**⚠ Corrected against `users/models.py` — the table below previously listed Teacher,
Parent, and a separate "School Admin" role that do not exist in the data model or the
public registration form. `CustomUser.USER_TYPE_CHOICES` currently defines exactly
three values: `user`, `student`, `admin`. Treat Teacher/Parent/School-Admin as roadmap
items, not shipped functionality, until the model and `RoleRegistrationForm` are
actually extended.**

| Role | Access |
|------|--------|
| Student (`student`) | Full: assessment, careers, AI coach, coaching plan — selectable at signup |
| General User (`user`) | Same core feature set as Student, without school/subject fields — selectable at signup |
| Admin (`admin`) | Analytics dashboard, assessment/career PDF reports, Django admin — not self-registrable; provisioned manually |

