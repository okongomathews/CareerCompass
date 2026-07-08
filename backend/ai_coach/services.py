"""
ai_coach/services.py
────────────────────
AI Coach with three-tier response strategy:
  Tier 1: OpenAI GPT (if OPENAI_API_KEY is configured)
  Tier 2: HuggingFace Inference API via google/flan-t5-large (free, no key required
           for limited use — or set HF_API_TOKEN for higher rate limits)
  Tier 3: Rich rule-based engine with Kenya-specific context (always works offline)

All tiers produce contextual, personalised responses using the student's
MBTI type, career recommendations, grade level, and learning style.
"""
import os
import re
import json
import random
import logging
import requests
from django.conf import settings
from assessments.models import AssessmentResult
from recommendations.models import LearningStyle, StudentRecommendation

logger = logging.getLogger(__name__)

# ── Tier 2: HuggingFace free inference endpoints ─────────────────────────────
HF_MODELS = [
    "google/flan-t5-large",            # Best for Q&A / instructions
    "HuggingFaceH4/zephyr-7b-beta",   # Better chat (needs token for full access)
    "mistralai/Mistral-7B-Instruct-v0.2",
]
HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/"


class AICoachService:
    def __init__(self, student):
        self.student = student
        self._load_student_context()

    # ── Context loading ───────────────────────────────────────────────────────
    def _load_student_context(self):
        self.assessment_result = None
        self.personality_type  = None
        self.top_careers       = []
        self.learning_style    = None

        try:
            self.assessment_result = AssessmentResult.objects.select_related(
                'personality_type').get(student=self.student)
            self.personality_type = self.assessment_result.personality_type
        except AssessmentResult.DoesNotExist:
            pass

        try:
            recs = StudentRecommendation.objects.filter(
                student=self.student
            ).select_related('career').order_by('-overall_score')[:3]
            self.top_careers = [r.career.name for r in recs]
        except Exception:
            pass

        try:
            from ai_coach.models import CoachingPlan
            cp = CoachingPlan.objects.get(student=self.student)
            self.learning_style = cp.learning_style
        except Exception:
            pass

    def get_learning_style_recommendation(self):
        """Map MBTI → recommended learning style."""
        LS_MAP = {
            'INTJ':'reading','INTP':'reading','ENTJ':'visual','ENTP':'kinesthetic',
            'INFJ':'reading','INFP':'reading','ENFJ':'auditory','ENFP':'kinesthetic',
            'ISTJ':'reading','ISFJ':'reading','ESTJ':'visual','ESFJ':'auditory',
            'ISTP':'kinesthetic','ISFP':'kinesthetic','ESTP':'kinesthetic','ESFP':'kinesthetic',
        }
        style_name = 'reading'
        if self.personality_type:
            style_name = LS_MAP.get(self.personality_type.mbti_type, 'reading')

        DESCRIPTIONS = {
            'visual':      'You learn best through diagrams, charts, videos, and visual representations.',
            'auditory':    'You learn best through discussions, lectures, podcasts, and verbal explanations.',
            'reading':     'You learn best through reading, writing notes, and structured text.',
            'kinesthetic': 'You learn best through hands-on practice, experiments, and active doing.',
        }
        try:
            return LearningStyle.objects.get(name=style_name)
        except LearningStyle.DoesNotExist:
            return LearningStyle.objects.create(
                name=style_name,
                description=DESCRIPTIONS.get(style_name, 'Balanced approach to learning.'),
                study_recommendations=self._get_study_recs(style_name)
            )

    def _get_study_recs(self, style):
        recs = {
            'visual':      'Use mind maps, colour-coded notes, infographics, YouTube tutorials.',
            'auditory':    'Record yourself, join study groups, listen to educational podcasts.',
            'reading':     'Take detailed written notes, read textbooks, write summaries.',
            'kinesthetic': 'Do practice problems, labs, projects; build things to understand them.',
        }
        return recs.get(style, 'Use a mix of methods and find what works best for you.')

    # ── Main entry point ──────────────────────────────────────────────────────
    def generate_ai_response(self, message, conversation_history=None):
        """
        Generate response using the best available tier.
        Returns a plain-text or markdown string.
        """
        system_prompt = self._build_system_prompt()
        history_text  = self._build_history_text(conversation_history)

        # Tier 1: OpenAI
        openai_key = getattr(settings, 'OPENAI_API_KEY', None) or os.getenv('OPENAI_API_KEY')
        if openai_key:
            resp = self._try_openai(system_prompt, history_text, message, openai_key)
            if resp:
                return resp

        # Tier 2: HuggingFace
        hf_token = getattr(settings, 'HF_API_TOKEN', None) or os.getenv('HF_API_TOKEN', '')
        resp = self._try_huggingface(system_prompt, history_text, message, hf_token)
        if resp:
            return resp

        # Tier 3: Rule-based
        return self._rule_based_response(message)

    # ── Tier 1: OpenAI ────────────────────────────────────────────────────────
    def _try_openai(self, system_prompt, history_text, message, api_key):
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)

            messages = [{"role": "system", "content": system_prompt}]
            if history_text:
                messages.append({"role": "user", "content": f"[Previous conversation context]\n{history_text}"})
                messages.append({"role": "assistant", "content": "Understood. I'll keep that context in mind."})
            messages.append({"role": "user", "content": message})

            model = getattr(settings, 'AI_MODEL', 'gpt-4o-mini')
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=getattr(settings, 'AI_MAX_TOKENS', 500),
                temperature=getattr(settings, 'AI_TEMPERATURE', 0.7),
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")
            return None

    # ── Tier 2: HuggingFace ───────────────────────────────────────────────────
    def _try_huggingface(self, system_prompt, history_text, message, token=''):
        """
        Try HuggingFace Inference API with flan-t5-large (free, no token needed
        for basic use). Falls through to next model on failure.
        """
        # Build a concise prompt for flan-t5 (instruction model)
        prompt = (
            f"You are a career guidance coach for Kenyan students. "
            f"Context: {system_prompt[:400]}\n"
            f"Student asks: {message}\n"
            f"Provide a helpful, specific answer in 3-5 sentences:"
        )

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        for model in HF_MODELS[:2]:   # try first two
            try:
                url  = HF_INFERENCE_URL + model
                data = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 300,
                        "temperature": 0.7,
                        "do_sample": True,
                        "return_full_text": False,
                    },
                    "options": {"wait_for_model": True},
                }
                r = requests.post(url, headers=headers, json=data, timeout=25)
                if r.status_code == 200:
                    result = r.json()
                    # flan-t5 returns [{"generated_text": "..."}]
                    if isinstance(result, list) and result:
                        text = result[0].get("generated_text", "").strip()
                        if text and len(text) > 20:
                            return self._clean_hf_response(text, message)
                    elif isinstance(result, dict):
                        text = result.get("generated_text", "").strip()
                        if text and len(text) > 20:
                            return self._clean_hf_response(text, message)
                elif r.status_code == 503:
                    # Model loading — try next
                    continue
            except Exception as e:
                logger.warning(f"HuggingFace {model} failed: {e}")
                continue
        return None

    def _clean_hf_response(self, text, original_message):
        """Post-process HF response to remove prompt leakage."""
        # Remove repeated prompt fragments
        for phrase in ["You are a career guidance", "Student asks:", "Provide a helpful"]:
            if phrase in text:
                parts = text.split(phrase)
                text = parts[-1].strip()
        # Trim leading punctuation artefacts
        text = re.sub(r'^[:\-\s]+', '', text).strip()
        if not text or len(text) < 15:
            return None
        return text

    # ── Tier 3: Rule-based ───────────────────────────────────────────────────
    def _build_system_prompt(self):
        name = self.student.user.first_name or self.student.user.username
        mbti = self.personality_type.mbti_type if self.personality_type else "unknown"
        mbti_name = self.personality_type.name if self.personality_type else ""
        careers = ", ".join(self.top_careers) if self.top_careers else "not yet determined"
        grade   = getattr(self.student, 'grade_level', 'secondary school') or 'secondary school'
        ls_name = self.learning_style.name if self.learning_style else "not yet assessed"

        return (
            f"You are CareerCompass AI Coach, an expert career guidance assistant "
            f"specialised in the Kenyan education system (KCSE, KUCCPS, universities). "
            f"You are helping {name}, a {grade} student. "
            f"Their MBTI personality type is {mbti} ({mbti_name}). "
            f"Their top recommended careers are: {careers}. "
            f"Their learning style is {ls_name}. "
            f"Always give specific, actionable advice relevant to Kenya. "
            f"Be encouraging, honest, and concise."
        )

    def _build_history_text(self, history_qs, max_msgs=6):
        if not history_qs:
            return ""
        try:
            recent = list(history_qs.order_by('-timestamp')[:max_msgs])[::-1]
            lines  = []
            for m in recent:
                role = "Coach" if m.is_from_ai else "Student"
                lines.append(f"{role}: {m.content[:200]}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _rule_based_response(self, message):
        """Comprehensive rule-based fallback with Kenya context."""
        ml = message.lower()
        name = self.student.user.first_name or "there"
        mbti = self.personality_type.mbti_type if self.personality_type else None

        # ── Greeting ──────────────────────────────────────────────────────────
        if any(w in ml for w in ['hello','hi','hey','good morning','good afternoon','good evening','habari','karibu']):
            greetings = [
                f"Hello {name}! 👋 I'm your CareerCompass AI Coach. I'm here to help you navigate career choices, "
                f"study strategies, and university pathways in Kenya. What would you like to explore today?",
                f"Karibu {name}! Great to have you here. Whether you're thinking about your KCSE subjects, "
                f"career paths, or university choices — I've got you covered. What's on your mind?",
            ]
            if mbti:
                greetings.append(
                    f"Hi {name}! As a {mbti} personality, you have some fantastic strengths we can build on. "
                    f"Ask me anything about careers, subjects, or your future!"
                )
            return random.choice(greetings)

        # ── Personality ───────────────────────────────────────────────────────
        if any(w in ml for w in ['personality','mbti','type','what am i','16 personalities']):
            return self._response_personality()

        # ── Career questions ──────────────────────────────────────────────────
        if any(w in ml for w in ['career','job','work','profession','best career','what career','which career','occupation']):
            return self._response_career(ml)

        # ── University / KUCCPS ───────────────────────────────────────────────
        if any(w in ml for w in ['university','college','kuccps','cluster','degree','diploma','course','admission']):
            return self._response_university(ml)

        # ── KCSE / Subjects ───────────────────────────────────────────────────
        if any(w in ml for w in ['kcse','subject','form','cluster points','combination','sciences','humanities']):
            return self._response_kcse(ml)

        # ── Study advice ──────────────────────────────────────────────────────
        if any(w in ml for w in ['study','learn','revise','revision','exam','tips','how to study','concentrate','focus']):
            return self._response_study(ml)

        # ── Motivation / Stress ───────────────────────────────────────────────
        if any(w in ml for w in ['stress','worried','scared','anxious','nervous','fail','failing','depressed','give up','discourage','motivat','hopeless']):
            return self._response_motivation(name)

        # ── Salary / Market ───────────────────────────────────────────────────
        if any(w in ml for w in ['salary','earn','pay','income','money','market','demand','jobs in kenya']):
            return self._response_salary_market(ml)

        # ── Learning style ────────────────────────────────────────────────────
        if any(w in ml for w in ['learning style','how do i learn','study method','best way to study']):
            return self._response_learning_style()

        # ── Specific subjects ─────────────────────────────────────────────────
        for subj, advice in SUBJECT_ADVICE.items():
            if subj in ml:
                return f"<strong>{subj.title()} in Kenya:</strong>\n\n{advice}"

        # ── Technology / Software ─────────────────────────────────────────────
        if any(w in ml for w in ['technology','software','it','computer','coding','programming','tech','developer']):
            return self._response_tech()

        # ── Healthcare ───────────────────────────────────────────────────────
        if any(w in ml for w in ['medicine','doctor','nurse','health','medical','clinical','pharmacy','dentist']):
            return self._response_healthcare()

        # ── Default contextual ────────────────────────────────────────────────
        return self._response_default(name, message)

    # ── Rule-based sub-methods ────────────────────────────────────────────────
    def _response_personality(self):
        if not self.personality_type:
            return (
                "You haven't completed the personality assessment yet. "
                "Head to <strong>Personality Test</strong> in the sidebar to discover your MBTI type — "
                "it takes 15–20 minutes and will unlock personalised career recommendations!"
            )
        pt = self.personality_type
        careers_text = pt.career_recommendations if pt.career_recommendations else "various fields"
        return (
            f"Your personality type is <strong>{pt.mbti_type} — {pt.name}</strong>. 🎯\n\n"
            f"<strong>Core strengths:</strong> {pt.strengths}\n\n"
            f"<strong>Areas to develop:</strong> {pt.weaknesses}\n\n"
            f"<strong>Career fields that suit {pt.mbti_type}s:</strong> {careers_text}\n\n"
            f"Want me to go deeper on any of these career paths or explain what being a "
            f"{pt.mbti_type} means for how you work and study?"
        )

    def _response_career(self, ml):
        if self.top_careers:
            careers_list = "\n".join(f"• {c}" for c in self.top_careers)
            intro = (
                f"Based on your {'<strong>' + self.personality_type.mbti_type + '</strong> personality and ' if self.personality_type else ''}"
                f"academic profile, your top recommended careers are:\n\n{careers_list}\n\n"
            )
        else:
            intro = "Complete your personality assessment to get personalised career recommendations. "

        # specific career queries
        if 'engineer' in ml:
            return intro + (
                "<strong>Engineering in Kenya</strong> is booming! Civil, electrical, software, and mechanical "
                "engineers are in high demand. KCSE requirements: A in Maths and Physics. "
                "Top universities: UoN, JKUAT, Strathmore. Starting salary: KES 80,000–150,000/month."
            )
        if 'medicine' in ml or 'doctor' in ml:
            return intro + (
                "<strong>Medicine in Kenya</strong> — one of the most respected and in-demand professions. "
                "Requires: A in Biology, Chemistry, Physics/Maths. Degree: 6 years at UoN, KU, MKU. "
                "Internship: 1 year mandatory. Specialist salary: KES 300,000+/month."
            )
        if 'business' in ml or 'finance' in ml or 'accounting' in ml:
            return intro + (
                "<strong>Business & Finance</strong> careers are diverse and well-paid in Kenya's growing economy. "
                "Options: Accounting (CPA-K), Finance, Marketing, Entrepreneurship. "
                "Consider STRATHMORE, KCA, KU for business degrees. CPA qualification opens many doors."
            )
        return intro + (
            "Kenya's fastest-growing sectors are: <strong>Technology</strong>, <strong>Healthcare</strong>, <strong>Finance</strong>, "
            "<strong>Education</strong>, and <strong>Construction</strong>. Visit the <strong>My Careers</strong> page to see your full "
            "personalised compatibility scores for 200+ Kenyan careers!"
        )

    def _response_university(self, ml):
        return (
            "<strong>University Pathways in Kenya:</strong>\n\n"
            "<strong>KUCCPS Process:</strong>\n"
            "1. Get your KCSE results (minimum C+ for most degree programmes)\n"
            "2. Apply via kuccps.ac.ke — three course choices per institution\n"
            "3. Cluster weights determine your eligibility for specific courses\n"
            "4. Accept placement and pay acceptance fee\n\n"
            "<strong>Top Public Universities:</strong> University of Nairobi (UoN), Kenyatta University (KU), "
            "Moi University, JKUAT, Egerton University, Maseno University\n\n"
            "<strong>Top Private Universities:</strong> Strathmore, USIU-Africa, Daystar, KCA\n\n"
            "<strong>Tip:</strong> Use the KUCCPS cluster calculator on their website to check your eligibility "
            "before applying. Would you like advice on a specific course or university?"
        )

    def _response_kcse(self, ml):
        return (
            "<strong>KCSE Subject Advice:</strong>\n\n"
            "<strong>Science Combination</strong> (for Engineering, Medicine, Sciences):\n"
            "Maths, Physics, Chemistry, Biology + any two others\n\n"
            "<strong>Business Combination</strong> (for Business, Economics, Law):\n"
            "Maths, Business Studies, Economics, English + Kiswahili + two others\n\n"
            "<strong>Arts/Humanities</strong> (for Education, Social Sciences, Media):\n"
            "History, Geography, CRE, Languages + Maths + Sciences\n\n"
            "<strong>Key KCSE Tips:</strong>\n"
            "→ Aim for minimum C+ overall and B+ in your cluster subjects\n"
            "→ Past papers from KNEC are your best revision tool\n"
            "→ Form 3 grades matter — don't wait for Form 4 to get serious\n\n"
            "What specific subject combination or career are you planning for?"
        )

    def _response_study(self, ml):
        ls_name = self.learning_style.name if self.learning_style else None
        tips = {
            'visual':      "📊 Use mind maps, colour-coded notes, flowcharts. Watch YouTube explanations. Draw diagrams to summarise topics.",
            'auditory':    "🎙️ Record yourself reading notes and replay them. Join or form discussion groups. Explain concepts aloud to yourself.",
            'reading':     "📚 Write detailed summaries after each topic. Use the Cornell note-taking method. Rewrite your notes in your own words.",
            'kinesthetic': "🔬 Do as many practice problems as possible. Build models, do experiments. Teach the concept to someone else.",
        }
        base = (
            "<strong>Effective Study Strategies for KCSE Success:</strong>\n\n"
            "1. <strong>Pomodoro Technique</strong> — 25 min focused study, 5 min break (repeat 4×, then 30 min break)\n"
            "2. <strong>Active Recall</strong> — Close your notes, write everything you remember. Then check.\n"
            "3. <strong>Spaced Repetition</strong> — Review notes after 1 day, 3 days, 1 week, 2 weeks\n"
            "4. <strong>Past Papers</strong> — Do at least 5 past papers per subject under exam conditions\n"
            "5. <strong>Teach Others</strong> — If you can explain it clearly, you've mastered it\n\n"
        )
        if ls_name and ls_name in tips:
            base += f"<strong>Personalised for your {ls_name.title()} learning style:</strong>\n{tips[ls_name]}\n\n"
        base += "Would you like specific study tips for a particular subject?"
        return base

    def _response_motivation(self, name):
        msgs = [
            f"I hear you, {name}. Feeling overwhelmed is completely normal — even the most "
            f"successful people go through tough patches. Here's what helps:\n\n"
            f"• <strong>Break it down</strong> — Focus on just the next 30 minutes, not the whole year\n"
            f"• <strong>Small wins</strong> — Tick off small tasks to build momentum\n"
            f"• <strong>Rest is productive</strong> — Sleep, exercise, and breaks improve performance\n"
            f"• <strong>Talk to someone</strong> — A teacher, parent, or friend can help lift the weight\n\n"
            f"Remember: Your KCSE grade is one chapter, not your whole story. "
            f"Kenya's job market rewards skills, resilience, and character — not just grades. 💪",

            f"{name}, I want you to know that where you are right now does not define where "
            f"you'll end up. Many of Kenya's most successful people struggled academically at some point.\n\n"
            f"What matters most right now: <strong>one good study session today</strong>. Just one. "
            f"Then another tomorrow. That's how mountains are climbed — one step at a time. 🌟",
        ]
        return random.choice(msgs)

    def _response_salary_market(self, ml):
        return (
            "<strong>Kenya Job Market — Key Salary Ranges (2025):</strong>\n\n"
            "💻 <strong>Technology:</strong> Software Developer KES 120,000–400,000 | Data Scientist 150,000–500,000\n"
            "🏥 <strong>Healthcare:</strong> Doctor 150,000–600,000 | Nurse 40,000–120,000 | Pharmacist 80,000–200,000\n"
            "⚖️ <strong>Law:</strong> Advocate 80,000–500,000+ | Legal Officer 60,000–150,000\n"
            "💰 <strong>Finance:</strong> Accountant 60,000–200,000 | Investment Banker 150,000–600,000\n"
            "🔧 <strong>Engineering:</strong> Civil 80,000–300,000 | Electrical 90,000–350,000\n"
            "📚 <strong>Education:</strong> Teacher (TSC) 30,000–80,000 | University Lecturer 100,000–250,000\n\n"
            "<strong>High-demand sectors 2025:</strong> AI/Tech, Renewable Energy, Healthcare, Finance, Construction\n\n"
            "Salaries vary by employer, experience, and location. Nairobi typically pays 20–40% more than other counties."
        )

    def _response_learning_style(self):
        if not self.learning_style:
            return (
                "I haven't determined your learning style yet — it's identified after your "
                "personality assessment. Complete the assessment to unlock personalised "
                "study strategies! 📖"
            )
        ls = self.learning_style
        return (
            f"Your learning style is <strong>{ls.name.title()}</strong>.\n\n"
            f"{ls.description}\n\n"
            f"<strong>Study recommendations:</strong> {ls.study_recommendations}\n\n"
            f"Matching your study method to your learning style can improve retention by up to 40%. "
            f"Would you like a personalised weekly study schedule?"
        )

    def _response_tech(self):
        return (
            "<strong>Technology Careers in Kenya 🇰🇪:</strong>\n\n"
            "Kenya is Africa's Silicon Savannah — tech careers are booming!\n\n"
            "<strong>Top paths:</strong>\n"
            "→ <strong>Software Engineering</strong> — Most in-demand; KES 120,000–400,000 entry-level\n"
            "→ <strong>Data Science/AI</strong> — Fastest growing; KES 150,000–500,000\n"
            "→ <strong>Cybersecurity</strong> — Critical shortage; KES 100,000–350,000\n"
            "→ <strong>Cloud Computing</strong> — AWS, Azure, Google Cloud certifications open doors globally\n"
            "→ <strong>Mobile Development</strong> — M-Pesa ecosystem; huge Kenya-specific demand\n\n"
            "<strong>Entry paths:</strong> Computer Science degree (JKUAT, UoN, Strathmore) OR "
            "bootcamps (Andela, Moringa School, Ajira Digital) — both work!\n\n"
            "<strong>Free learning resources:</strong> freeCodeCamp, The Odin Project, Google Career Certificates"
        )

    def _response_healthcare(self):
        return (
            "<strong>Healthcare Careers in Kenya:</strong>\n\n"
            "Healthcare is one of Kenya's most stable and respected fields.\n\n"
            "<strong>Popular paths:</strong>\n"
            "→ <strong>Medicine (MBChB)</strong> — 6 years | C+ in Bio, Chem, Phys/Maths | UoN, KU, MKU\n"
            "→ <strong>Nursing</strong> — 4 years (BScN) or 3 years diploma | Strong job market Kenya & abroad\n"
            "→ <strong>Pharmacy</strong> — 5 years | Good KCSE sciences required\n"
            "→ <strong>Medical Lab Science</strong> — 4 years | Growing demand\n"
            "→ <strong>Physiotherapy</strong> — 4 years | Emerging market\n"
            "→ <strong>Public Health</strong> — 4 years | NGOs, government, WHO opportunities\n\n"
            "<strong>Tip:</strong> Kenyan nurses and doctors are in demand internationally "
            "(UK NHS, Middle East, Canada) — a Kenyan degree opens global doors."
        )

    def _response_default(self, name, message):
        if self.personality_type:
            return (
                f"That's a great question, {name}! As a <strong>{self.personality_type.mbti_type}</strong>, "
                f"you likely approach this with {self.personality_type.strengths.split(',')[0].lower()}. "
                f"I'd be happy to give you more specific guidance — could you tell me a bit more about "
                f"what aspect of careers or studying you'd like help with?\n\n"
                f"Or explore these topics: <strong>career paths</strong>, <strong>KCSE subject choices</strong>, "
                f"<strong>university applications</strong>, <strong>study tips</strong>, or <strong>job market in Kenya</strong>."
            )
        return (
            f"Thanks for your question, {name}! I'm here to help with career guidance, "
            f"study strategies, and navigating Kenya's education system.\n\n"
            f"You can ask me about: <strong>career recommendations</strong>, <strong>KCSE subjects</strong>, "
            f"<strong>university choices</strong>, <strong>study tips</strong>, <strong>salary information</strong>, or anything "
            f"related to your future. What would you like to know?"
        )

    # ── Coaching plan generation ───────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    # Coaching Plan Generation — user-type aware
    # Detects: secondary student, university student, working professional,
    # career changer, gap-year, and general (non-student) user.
    # ─────────────────────────────────────────────────────────────────────────

    def _user_context(self):
        """Return a dict describing what kind of user this is."""
        try:
            user      = self.student.user
            user_type = getattr(user, 'user_type', 'student')
            grade     = getattr(self.student, 'grade_level', '') or ''
        except Exception:
            user_type, grade = 'student', ''

        # Categorise
        is_secondary   = grade in ('form1', 'form2', 'form3', 'form4',
                                    'form4_complete')
        is_university  = grade.startswith('year')
        is_gap_year    = grade == 'gap_year'
        is_general     = user_type in ('user', 'admin') or (
                            user_type == 'student' and not grade)
        is_professional = is_general and not is_secondary and not is_university

        return {
            'user_type':       user_type,
            'grade':           grade,
            'is_secondary':    is_secondary,
            'is_university':   is_university,
            'is_gap_year':     is_gap_year,
            'is_general':      is_general,
            'is_professional': is_professional,
        }

    def generate_coaching_plan(self, coaching_plan):
        """
        Populate a CoachingPlan with content tailored to the user's context:
        secondary school student, university student, working professional,
        gap-year, or general user.  KCSE-specific advice is only generated
        for secondary students.
        """
        if not self.personality_type:
            return None

        pt      = self.personality_type
        careers = self.top_careers
        ls      = self.get_learning_style_recommendation()
        ctx     = self._user_context()

        strengths  = [s.strip() for s in (pt.strengths  or '').split(',') if s.strip()][:5]
        weaknesses = [w.strip() for w in (pt.weaknesses or '').split(',') if w.strip()][:4]

        short_g  = coaching_plan.short_term_goals  or self._default_short_term_goals(pt, careers, ctx)
        medium_g = coaching_plan.medium_term_goals or self._default_medium_term_goals(pt, careers, ctx)
        long_g   = coaching_plan.long_term_goals   or self._default_long_term_goals(pt, careers, ctx)

        coaching_plan.personality_type      = pt
        coaching_plan.learning_style        = ls
        coaching_plan.short_term_goals      = short_g
        coaching_plan.medium_term_goals     = medium_g
        coaching_plan.long_term_goals       = long_g
        coaching_plan.key_strengths         = strengths
        coaching_plan.identified_challenges = weaknesses
        coaching_plan.action_items          = self._generate_action_items(pt, careers, ls, ctx)
        coaching_plan.save()
        return coaching_plan

    def _default_short_term_goals(self, pt, careers, ctx):
        top = careers[0] if careers else 'your target career'

        if ctx['is_secondary']:
            goals = [
                f"Research the day-to-day responsibilities and entry requirements for a {top}",
                f"Find out which KCSE subjects are required for a career as a {top}",
                "Discuss your career interests with a teacher, parent, or school counsellor",
            ]
            if 'N' in pt.mbti_type:
                goals.append("Explore free online courses (Khan Academy, Coursera) in your area of interest")
            else:
                goals.append("Visit or shadow a professional working in your target career field")

        elif ctx['is_university']:
            goals = [
                f"Identify internship or attachment opportunities related to {top} for the upcoming semester",
                "Connect with 3 professionals in your field on LinkedIn",
                f"Join a university club or society relevant to {top}",
            ]
            if 'N' in pt.mbti_type:
                goals.append("Start a side project or research paper in your area of specialisation")
            else:
                goals.append("Attend at least one industry event or career fair this semester")

        elif ctx['is_gap_year']:
            goals = [
                f"Use this gap year to confirm your interest in {top} through volunteering or shadowing",
                "Research university or college programmes that lead to your career goal",
                "Build a practical skill relevant to your field (online course, workshop, or self-study)",
                "Create a structured daily schedule to stay productive during your gap year",
            ]

        else:
            # Professional / general user / career changer
            goals = [
                f"Map out the skills gap between your current experience and a role as a {top}",
                f"Identify 2–3 short courses or certifications that would strengthen your {top} profile",
                "Update your CV and LinkedIn profile to reflect your career direction",
            ]
            if 'E' in pt.mbti_type:
                goals.append(f"Attend a networking event or industry meetup related to {top} in the next month")
            else:
                goals.append(f"Join an online community or forum for professionals in the {top} field")

        return goals

    def _default_medium_term_goals(self, pt, careers, ctx):
        top = careers[0] if careers else 'your target field'

        if ctx['is_secondary']:
            goals = [
                f"Achieve the KCSE grades required to qualify for a {top} programme",
                f"Apply to at least 3 universities or colleges offering {top}-related programmes",
                "Complete a relevant internship, attachment, or work-experience opportunity",
            ]
            if 'E' in pt.mbti_type:
                goals.append("Take on a leadership role in a school club related to your career interest")
            else:
                goals.append("Complete an online certification course in your field of interest")

        elif ctx['is_university']:
            goals = [
                f"Complete a formal internship or industrial attachment in the {top} field",
                "Build a portfolio of projects, research papers, or achievements to show employers",
                f"Secure a part-time role or freelance work related to {top}",
                "Achieve a minimum GPA of 3.0 (Upper Second Class Honours equivalent)",
            ]

        elif ctx['is_gap_year']:
            goals = [
                f"Enrol in a university, college, or TVET programme leading towards {top}",
                "Complete a short course or online certification to demonstrate commitment",
                "Build savings or secure a scholarship/loan to fund your education",
            ]

        else:
            goals = [
                f"Secure a role as a {top} or make a lateral move into the field",
                "Complete a recognised professional qualification or certification in your field",
                "Build a reputation through published work, speaking, or community contribution",
            ]
            if 'E' in pt.mbti_type:
                goals.append("Grow your professional network by attending or organising industry events")
            else:
                goals.append("Develop expertise in a niche area of your field and document it online")

        return goals

    def _default_long_term_goals(self, pt, careers, ctx):
        top = careers[0] if careers else 'your chosen career'

        if ctx['is_secondary']:
            return [
                f"Graduate from university with a qualification in {top} or a related field",
                "Secure your first professional role in your chosen career",
                "Achieve financial independence through a fulfilling and well-paid career",
                f"Become a respected practitioner or expert in the {top} field in Kenya",
            ]
        elif ctx['is_university']:
            return [
                f"Graduate and secure your first full-time role as a {top}",
                "Build 3–5 years of experience and progress to a mid-level position",
                "Pay off any student loans and build a solid financial foundation",
                f"Mentor others entering the {top} profession",
            ]
        elif ctx['is_gap_year']:
            return [
                f"Complete your education and qualify as a {top}",
                "Gain enough experience to be financially self-sustaining",
                "Look back on your gap year as a productive pivot, not wasted time",
            ]
        else:
            return [
                f"Establish yourself as a senior-level {top} with a strong professional track record",
                "Build passive income streams or business ventures alongside your career",
                "Share your knowledge by mentoring junior professionals in your field",
                "Achieve work-life balance and personal fulfilment alongside career success",
            ]

    def _generate_action_items(self, pt, careers, ls, ctx):
        top = careers[0] if careers else 'your target career'
        ls_name = ls.name if ls else 'your preferred'

        if ctx['is_secondary']:
            items = [
                f"Visit KUCCPS (kuccps.ac.ke) to check minimum cluster points required for {top} programmes",
                "Download KNEC past papers for your 3 weakest KCSE subjects and complete one paper this week",
                f"Search LinkedIn for professionals working as {top}s in Kenya and read their career stories",
                f"Create a weekly study timetable aligned to your {ls_name} learning style",
                "Write a one-paragraph personal statement explaining why you want to pursue this career",
            ]
            if 'T' in pt.mbti_type:
                items.append("Build a spreadsheet tracking KUCCPS cut-off points, deadlines, and application status")
            else:
                items.append("Talk to your school counsellor or a trusted adult about your career plan this week")

        elif ctx['is_university']:
            items = [
                f"Search Brighter Monday, LinkedIn, and Fuzu for {top} internships and save 5 listings",
                "Update your LinkedIn profile with your current university, skills, and career interests",
                f"Reach out to one professional in the {top} field for an informational interview",
                "Attend the next career fair or industry event at your institution",
                f"Identify one open-source project, research opportunity, or competition related to {top}",
            ]
            if 'T' in pt.mbti_type:
                items.append("Build a project portfolio or GitHub repository to showcase your work")
            else:
                items.append("Join a study group or professional association in your field")

        elif ctx['is_gap_year']:
            items = [
                "Create a structured daily routine with dedicated time for learning and skill-building",
                f"Complete one free online course related to {top} on Coursera, edX, or Alison",
                "Research at least 5 university or college programmes aligned to your career goal",
                "Explore volunteer opportunities that give you relevant experience",
                "Set a savings goal or research scholarships to fund your next steps",
            ]

        else:
            # Professional / general user
            items = [
                f"Search Fuzu, LinkedIn, and BrighterMonday for {top} roles and note required skills",
                "Identify one professional certification that would strengthen your {top} application",
                "Update your CV and LinkedIn headline to clearly reflect your {top} career direction",
                f"Connect with 5 {top} professionals on LinkedIn this week",
                "Set aside 30 minutes daily for learning (reading, podcasts, or online courses)",
            ]
            if 'T' in pt.mbti_type:
                items.append("Build a skills-gap tracker comparing your current CV to 3 target job descriptions")
            else:
                items.append("Find a mentor or career coach who works in your target field")

        return items


# ── Subject-specific advice dictionary ───────────────────────────────────────
SUBJECT_ADVICE = {
    'mathematics': (
        "Mathematics is the gateway to Engineering, Data Science, Finance, and Architecture. "
        "<strong>KCSE Tips:</strong> Practice past papers daily (KNEC papers 2014–2023 are online free). "
        "Focus on Algebra, Calculus, Statistics. Aim for A (80+) for Engineering/Medicine pathways. "
        "Free resources: Khan Academy, mathway.com"
    ),
    'physics': (
        "Physics is essential for Engineering, Architecture, and Physical Sciences. "
        "<strong>KCSE Tips:</strong> Understand concepts before memorising formulas. Draw diagrams. "
        "Form 4 topics: Electricity, Electronics, Radioactivity are heavily tested. "
        "Watch 'Physics with Professor Dave' on YouTube for clear explanations."
    ),
    'chemistry': (
        "Chemistry is required for Medicine, Pharmacy, Chemical Engineering, Food Science. "
        "<strong>KCSE Tips:</strong> Organic Chemistry (Form 4) is the hardest — start early. "
        "Memorise the periodic table properties. Balance every equation. "
        "Do at least 10 KNEC past papers under timed conditions."
    ),
    'biology': (
        "Biology opens doors to Medicine, Nursing, Agriculture, Environmental Science. "
        "<strong>KCSE Tips:</strong> Ecology (Form 3) and Genetics (Form 4) need special attention. "
        "Draw and label diagrams accurately — examiners reward detail. "
        "Use Longhorn and KLB Biology revision guides."
    ),
    'english': (
        "English is compulsory and critical for ALL university courses. "
        "<strong>KCSE Tips:</strong> Section A (comprehension) — read question BEFORE the passage. "
        "Composition: plan with a paragraph structure before writing. "
        "Grammar: master tenses, reported speech, conditionals — they're always tested."
    ),
    'history': (
        "History opens careers in Law, Politics, Journalism, International Relations, Teaching. "
        "<strong>KCSE Tips:</strong> Form 4 Kenya History (post-independence) is heavily tested. "
        "Learn dates and cause-effect relationships, not just facts. "
        "Structure essays with Introduction-Evidence-Analysis-Conclusion."
    ),
    'geography': (
        "Geography combines well with Environmental Science, Urban Planning, Meteorology, Teaching. "
        "<strong>KCSE Tips:</strong> Physical Geography (weather, soils) and Human Geography (population, agriculture). "
        "Map reading questions appear every year — practise contour interpretation. "
        "Use diagrams and statistics in your answers."
    ),
    'business': (
        "Business Studies is perfect for Commerce, Accounting, Marketing, Entrepreneurship. "
        "<strong>KCSE Tips:</strong> Form 4 topics (partnership, limited companies, source documents) are key. "
        "Practise double-entry bookkeeping until it's automatic. "
        "Consider CPA-K (accounting certification) after KCSE — very marketable in Kenya."
    ),
    'computer': (
        "Computer Studies is increasingly valuable and directly links to Kenya's ICT sector. "
        "<strong>KCSE Tips:</strong> Programming (Pascal/Python), Data Processing, Networks are tested. "
        "Learn beyond the syllabus — JavaScript, Python basics from freeCodeCamp are free. "
        "Ajira Digital and Google Africa certification programmes are free post-KCSE options."
    ),
}
