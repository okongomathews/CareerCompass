"""
load_mbti_data.py
─────────────────────────────────────────────────────────────────────────────
Comprehensive MBTI data loader for CareerCompass Kenya.

Populates:
  • 4 MBTIDimension objects
  • 16 PersonalityType objects (with Kenyan-context descriptions)
  • 60 Questions  – 15 per dimension, none leading toward either pole
  • 7 AnswerChoices per Question  (strongly agree … strongly disagree)

Question design principles (Isabel Briggs Myers / CPP research):
  • Each question describes a **natural tendency or preference**, not a value.
  • Neither option should sound virtuous or culturally superior.
  • Questions are worded in everyday language, not occupational language.
  • Odd-numbered questions lean toward the A-pole; even toward B-pole so
    acquiescence bias is neutralised.
  • Scenarios cover home, social, academic, and general daily-life contexts.

Run:
    python manage.py load_mbti_data
    python manage.py load_mbti_data --clear   # wipe & reload
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import MBTIDimension, Question, AnswerChoice, PersonalityType


# ─────────────────────────────────────────────────────────────────────────────
# PERSONALITY TYPES  (all 16)
# ─────────────────────────────────────────────────────────────────────────────
PERSONALITY_TYPES = [
    {
        "mbti_type": "INTJ",
        "name": "The Architect",
        "description": (
            "INTJs are analytical strategists who combine visionary thinking with "
            "decisive action. They see systems and patterns where others see chaos, "
            "and quietly build long-range plans to achieve ambitious goals. "
            "In Kenya's context, INTJs often excel in research institutions, policy "
            "development, software engineering, and entrepreneurship."
        ),
        "strengths": (
            "Strategic long-range thinking, independent problem solving, high standards, "
            "decisive under pressure, ability to synthesise complex information, "
            "self-confidence, innovative mindset"
        ),
        "weaknesses": (
            "Can seem arrogant or dismissive of others' feelings, dislikes routine tasks, "
            "may struggle to communicate vision to others, overly critical of inefficiency, "
            "reluctant to ask for help"
        ),
        "career_recommendations": (
            "Software Engineer, Data Scientist, Strategic Planner, Economist, "
            "Research Scientist, Investment Analyst, Architect, University Lecturer"
        ),
    },
    {
        "mbti_type": "INTP",
        "name": "The Logician",
        "description": (
            "INTPs are inventive thinkers driven by a relentless curiosity to understand "
            "how everything works. They love exploring theoretical frameworks and finding "
            "elegant solutions to complex problems. In Kenya, INTPs thrive in academia, "
            "technology, and scientific research."
        ),
        "strengths": (
            "Deep analytical thinking, creativity in problem solving, open-mindedness, "
            "objectivity, intellectual curiosity, ability to see multiple perspectives"
        ),
        "weaknesses": (
            "Procrastination, difficulty with deadlines, poor attention to practical details, "
            "insensitivity to emotional needs, can be condescending, struggles with routine"
        ),
        "career_recommendations": (
            "Software Developer, Research Scientist, Mathematician, Data Analyst, "
            "University Lecturer, Systems Analyst, Philosopher, Forensic Scientist"
        ),
    },
    {
        "mbti_type": "ENTJ",
        "name": "The Commander",
        "description": (
            "ENTJs are natural-born leaders who combine bold vision with strategic "
            "execution. They are energised by challenges and have a talent for rallying "
            "people around a common goal. In Kenya, ENTJs are drawn to executive roles, "
            "law, entrepreneurship, and leadership in government or business."
        ),
        "strengths": (
            "Strong leadership, strategic vision, efficiency, confidence, decisiveness, "
            "motivating others, long-term planning, high energy"
        ),
        "weaknesses": (
            "Impatience with others, may seem domineering, dismissive of emotions, "
            "intolerant of inefficiency, may take on too much, arrogance risk"
        ),
        "career_recommendations": (
            "Chief Executive Officer, Lawyer, Entrepreneur, Management Consultant, "
            "Financial Director, Political Leader, Military Officer, University Dean"
        ),
    },
    {
        "mbti_type": "ENTP",
        "name": "The Debater",
        "description": (
            "ENTPs are quick-witted innovators who love a good intellectual challenge. "
            "They are energised by debating ideas, spotting logical gaps, and pioneering "
            "new approaches. In Kenya, ENTPs thrive in law, media, technology start-ups, "
            "and entrepreneurship."
        ),
        "strengths": (
            "Creative problem solving, quick thinking, persuasiveness, adaptability, "
            "broad knowledge, innovation, seeing possibilities others miss"
        ),
        "weaknesses": (
            "Difficulty following through, argumentative, easily bored, poor with routine, "
            "insensitive to feelings, may spread energy too thin"
        ),
        "career_recommendations": (
            "Lawyer, Journalist, Entrepreneur, Marketing Director, Consultant, "
            "Product Manager, Software Architect, Policy Analyst"
        ),
    },
    {
        "mbti_type": "INFJ",
        "name": "The Advocate",
        "description": (
            "INFJs are rare idealists with a powerful sense of purpose and deep empathy. "
            "They combine creative vision with quiet determination to make a meaningful "
            "difference. In Kenya, INFJs are drawn to counselling, social work, "
            "education, and non-profit leadership."
        ),
        "strengths": (
            "Deep empathy, purposefulness, creativity, insight into others, "
            "perseverance, strong values, ability to inspire"
        ),
        "weaknesses": (
            "Perfectionism, burnout risk, difficulty with criticism, can be secretive, "
            "overly idealistic, reluctant to share feelings"
        ),
        "career_recommendations": (
            "Counsellor/Therapist, Social Worker, Doctor, Nurse, Teacher, "
            "Non-profit Director, Writer, Human Rights Lawyer"
        ),
    },
    {
        "mbti_type": "INFP",
        "name": "The Mediator",
        "description": (
            "INFPs are deeply idealistic and empathetic individuals guided by strong "
            "personal values. They have a gift for understanding others' feelings and "
            "a passion for creative expression. In Kenya, INFPs find purpose in "
            "arts, education, counselling, and humanitarian work."
        ),
        "strengths": (
            "Empathy, open-mindedness, creativity, dedication to values, "
            "passion, flexibility, ability to see good in others"
        ),
        "weaknesses": (
            "Over-idealism, avoidance of conflict, difficulty with criticism, "
            "poor with practical tasks, emotional vulnerability, procrastination"
        ),
        "career_recommendations": (
            "Writer/Author, Counsellor, Social Worker, Teacher, Graphic Designer, "
            "Musician, Community Development Officer, Humanitarian Aid Worker"
        ),
    },
    {
        "mbti_type": "ENFJ",
        "name": "The Protagonist",
        "description": (
            "ENFJs are charismatic, empathetic leaders who inspire others toward growth "
            "and collaboration. They are deeply invested in the wellbeing of those around "
            "them. In Kenya, ENFJs thrive in teaching, community leadership, health, "
            "and human resources."
        ),
        "strengths": (
            "Charisma, empathy, strong communication, ability to inspire, "
            "organisational skills, warmth, commitment to others' growth"
        ),
        "weaknesses": (
            "Over-involvement in others' problems, people-pleasing, difficulty with "
            "tough decisions, burnout from over-giving, overly idealistic"
        ),
        "career_recommendations": (
            "Teacher, Human Resources Manager, Community Development Officer, "
            "Counsellor, Doctor, Politician, Non-profit Manager, Social Entrepreneur"
        ),
    },
    {
        "mbti_type": "ENFP",
        "name": "The Campaigner",
        "description": (
            "ENFPs are enthusiastic, creative free spirits who see life as full of "
            "possibilities. They love connecting with people and generating new ideas. "
            "In Kenya, ENFPs excel in marketing, media, education, and entrepreneurship."
        ),
        "strengths": (
            "Enthusiasm, creativity, excellent communication, empathy, "
            "adaptability, seeing potential in others, inspirational energy"
        ),
        "weaknesses": (
            "Difficulty with follow-through, poor with routine, over-optimism, "
            "emotional sensitivity, scattered focus, dislike of constraints"
        ),
        "career_recommendations": (
            "Marketing Manager, Journalist, Teacher, Entrepreneur, "
            "Public Relations Officer, Media Producer, Counsellor, Brand Strategist"
        ),
    },
    {
        "mbti_type": "ISTJ",
        "name": "The Logistician",
        "description": (
            "ISTJs are reliable, methodical individuals who take their responsibilities "
            "seriously. They are the backbone of institutions and excel at ensuring "
            "systems run correctly. In Kenya, ISTJs excel in accounting, law, "
            "administration, engineering, and the military."
        ),
        "strengths": (
            "Reliability, thoroughness, strong work ethic, integrity, practicality, "
            "attention to detail, patience, loyalty"
        ),
        "weaknesses": (
            "Resistance to change, inflexibility, can seem cold, difficulty with "
            "ambiguity, may over-rely on past methods, workaholic tendencies"
        ),
        "career_recommendations": (
            "Accountant, Civil Servant, Auditor, Military Officer, Police Officer, "
            "Engineer, Database Administrator, Supply Chain Manager"
        ),
    },
    {
        "mbti_type": "ISFJ",
        "name": "The Defender",
        "description": (
            "ISFJs are warm, dedicated individuals who are deeply committed to caring "
            "for others and fulfilling their responsibilities. In Kenya, ISFJs are "
            "valued in nursing, teaching, social work, and community healthcare."
        ),
        "strengths": (
            "Reliability, warmth, patience, attention to detail, strong work ethic, "
            "empathy, loyalty, memory for personal details"
        ),
        "weaknesses": (
            "Reluctance to say no, internalising stress, resistance to change, "
            "undervaluing themselves, difficulty expressing emotions"
        ),
        "career_recommendations": (
            "Nurse, Primary School Teacher, Social Worker, Medical Lab Technician, "
            "Pharmacist, Community Health Worker, Office Manager, Librarian"
        ),
    },
    {
        "mbti_type": "ESTJ",
        "name": "The Executive",
        "description": (
            "ESTJs are no-nonsense organisers who believe in rules, order, and getting "
            "things done. They are natural managers and administrators. In Kenya, ESTJs "
            "excel in business management, government, law enforcement, and finance."
        ),
        "strengths": (
            "Organisation, decisiveness, reliability, leadership, strong work ethic, "
            "directness, loyalty, ability to implement plans"
        ),
        "weaknesses": (
            "Inflexibility, judgmental of non-conformists, difficulty with emotions, "
            "status-consciousness, resistance to new approaches"
        ),
        "career_recommendations": (
            "Business Manager, Government Administrator, Police Commander, "
            "Financial Controller, Supply Chain Director, School Principal, Judge"
        ),
    },
    {
        "mbti_type": "ESFJ",
        "name": "The Consul",
        "description": (
            "ESFJs are caring, sociable individuals who are deeply invested in "
            "the harmony and wellbeing of their communities. In Kenya, ESFJs "
            "are natural fits for nursing, teaching, and community-facing roles."
        ),
        "strengths": (
            "Warmth, loyalty, generosity, strong social skills, dependability, "
            "organisational ability, sensitivity to others' needs"
        ),
        "weaknesses": (
            "Sensitivity to criticism, difficulty with change, can be controlling, "
            "approval-seeking, reluctant to innovate, difficulty with conflict"
        ),
        "career_recommendations": (
            "Nurse, Primary Teacher, Hotel Manager, Sales Representative, "
            "HR Officer, Community Liaison, Medical Receptionist, Social Worker"
        ),
    },
    {
        "mbti_type": "ISTP",
        "name": "The Virtuoso",
        "description": (
            "ISTPs are hands-on troubleshooters who love understanding how things "
            "work through direct observation and experimentation. In Kenya, ISTPs "
            "excel as mechanics, engineers, pilots, and forensic professionals."
        ),
        "strengths": (
            "Practical problem solving, mechanical aptitude, calm under pressure, "
            "adaptability, efficiency, observational skills, resourcefulness"
        ),
        "weaknesses": (
            "Commitment avoidance, insensitivity, risk-taking, impatience with "
            "theory, private to the point of seeming cold, dislikes long-term planning"
        ),
        "career_recommendations": (
            "Mechanical Engineer, Pilot, Forensic Scientist, Electrician, "
            "Software Developer, Surgeon, Military Specialist, Athletics Coach"
        ),
    },
    {
        "mbti_type": "ISFP",
        "name": "The Adventurer",
        "description": (
            "ISFPs are gentle, spontaneous artists who experience the world through "
            "sensation and feeling. They have strong aesthetic sense and deep empathy. "
            "In Kenya, ISFPs find purpose in arts, craft, healthcare, and conservation."
        ),
        "strengths": (
            "Creativity, empathy, flexibility, strong aesthetic sense, "
            "loyalty to those they care about, present-moment awareness"
        ),
        "weaknesses": (
            "Conflict avoidance, difficulty planning ahead, vulnerability to criticism, "
            "difficulty with abstract theory, may keep too much to themselves"
        ),
        "career_recommendations": (
            "Graphic Designer, Musician, Nurse, Wildlife Conservationist, "
            "Fashion Designer, Artisan Craftsperson, Physiotherapist, Photographer"
        ),
    },
    {
        "mbti_type": "ESTP",
        "name": "The Entrepreneur",
        "description": (
            "ESTPs are bold, energetic pragmatists who live in the moment and are "
            "energised by action and results. They are perceptive and quick to "
            "capitalise on opportunities. In Kenya, ESTPs thrive in sales, "
            "entrepreneurship, and frontline business."
        ),
        "strengths": (
            "Action-orientation, boldness, perceptiveness, persuasiveness, "
            "adaptability, resourcefulness, networking ability, practical intelligence"
        ),
        "weaknesses": (
            "Impatience, risk-taking, insensitivity, poor long-term planning, "
            "difficulty with abstract rules, can be manipulative"
        ),
        "career_recommendations": (
            "Entrepreneur, Sales Director, Real Estate Agent, Paramedic, "
            "Detective, Marketing Executive, Stock Broker, Sports Athlete"
        ),
    },
    {
        "mbti_type": "ESFP",
        "name": "The Entertainer",
        "description": (
            "ESFPs are spontaneous, energetic, and enthusiastic performers who "
            "love people and experience. They live in the moment and bring joy "
            "to those around them. In Kenya, ESFPs shine in entertainment, "
            "hospitality, teaching young children, and event management."
        ),
        "strengths": (
            "Enthusiasm, people skills, adaptability, observational ability, "
            "creativity, generosity, practical skills, natural warmth"
        ),
        "weaknesses": (
            "Easily bored, avoidance of conflict, poor long-term planning, "
            "difficulty with abstract theory, sensitivity to criticism, impulsiveness"
        ),
        "career_recommendations": (
            "Events Manager, Early Childhood Teacher, Actor/Presenter, "
            "Hotel/Tourism Manager, Nurse, Sales Representative, Sports Coach, Musician"
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# QUESTIONS  – 120 total, 30 per dimension (expanded from 60 for higher accuracy)
# Research basis: MBTI Form M uses 93 items; 30 items/dimension achieves
# Cronbach α > 0.85 (Myers, McCaulley, Quenk & Hammer, 1998).
# dimension_a_weight = weight toward A-pole (E, S, T, J)
# dimension_b_weight = weight toward B-pole (I, N, F, P)
# Both weights = 1; scoring done via answer value (-3 to +3)
# Positive answer value → A-pole; negative → B-pole
# Odd questions lean A-pole; even questions lean B-pole
# ─────────────────────────────────────────────────────────────────────────────
QUESTIONS = [
    # ═══════════════════════════════════════════════════════════════════════════
    # E / I  —  Extraversion vs Introversion  (23 questions)
    # Research: MBTI Form M ~23 items/dim, Cronbach α 0.91–0.92
    # 5 facets: Energy Source | Social Breadth/Depth | Communication Style |
    #           Initiative | Environment Preference
    # A-pole (E): sociable, action-before-reflection, breadth, external
    # B-pole (I): reserved, reflection-before-action, depth, internal
    # Odd index (0,2,4…) = A-pole; Even index (1,3,5…) = B-pole
    # ═══════════════════════════════════════════════════════════════════════════

    # Facet 1 — Energy Source
    {"text": "After spending several hours at a lively social gathering, you feel energised rather than drained.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "After a long day of classes or work, you recover best by having quiet time alone rather than going out.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Being around other people for an extended period gives you more energy than it takes away.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When you are feeling low or stressed, spending time alone helps you feel better more than talking to others.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 2 — Social Breadth vs Depth
    {"text": "You prefer having a wide network of acquaintances and connections over a small tight-knit group of close friends.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You prefer having a small number of very close friends to a wide circle of many acquaintances.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find it easy and natural to start conversations with people you have just met.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You tend to keep personal thoughts and feelings to yourself until you know someone very well.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 3 — Communication Style
    {"text": "You often figure out what you think about something by talking it through with others.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You prefer to think things through fully on your own before sharing your views with others.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "In group discussions or meetings, you tend to speak up and contribute your views early rather than waiting to hear others first.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When you need to communicate something important, you prefer to write it down rather than say it in person.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 4 — Initiative
    {"text": "When a group needs someone to take charge of a discussion or activity, you are comfortable stepping into that role rather than waiting for someone else.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "In a new group or situation, you prefer to observe and listen for a while before you start contributing.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You learn best by doing and participating actively, rather than by watching or reading first.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Before starting a new task, you like to take time to think and plan rather than jumping straight in.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 5 — Environment Preference
    {"text": "You generally work and think better when there is background activity and noise around you.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You concentrate and produce your best work when you are alone in a quiet environment.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Working and brainstorming in a group brings out ideas and energy in you that working alone does not.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find that you are most productive and creative when working independently, without others around.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You actively seek out new experiences, people, and situations to keep life interesting and engaging.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find more satisfaction in exploring a few interests deeply than in constantly trying new things.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You feel comfortable being the centre of attention in social situations, such as speaking in front of a group.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When you have something important to say, you find it more natural to write it down — in a message, journal, or email — than to say it aloud in a group.", "category": "EI", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # ═══════════════════════════════════════════════════════════════════════════
    # S / N  —  Sensing vs Intuition  (23 questions)
    # 5 facets: Detail/Big Picture | Time Orientation | Concrete/Abstract |
    #           Memory Style | Routine/Innovation
    # A-pole (S): concrete, detail, present, practical, experiential
    # B-pole (N): abstract, pattern, future, theoretical, imaginative
    # ═══════════════════════════════════════════════════════════════════════════

    # Facet 1 — Detail vs Big Picture
    {"text": "When given a task, you pay close attention to the specific details and instructions rather than the general idea.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When given a task, you focus more on the overall goal and meaning than on the specific details of how to do it.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You tend to notice when something is slightly different or out of place, even if others do not.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You naturally see patterns and connections between things that seem unrelated to most other people.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 2 — Time Orientation (present vs future)
    {"text": "You are more focused on dealing with what is real and present in front of you than on imagining what could be.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You spend considerable time thinking about future possibilities and what things could become.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You trust what has been tried and tested more than untested new approaches or ideas.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are more excited by new, untested ideas and possibilities than by what has already been proven to work.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 3 — Concrete vs Abstract
    {"text": "You prefer clear, literal, step-by-step instructions to vague or metaphorical ones.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are naturally drawn to metaphors, symbols, and abstract ideas rather than concrete literal descriptions.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When learning something new, you want to know the practical application of it before worrying about the theory.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find it more satisfying to understand why something works than simply to know how to do it.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 4 — Memory and Information Processing
    {"text": "You have a good memory for specific facts, dates, names, and details from your past experiences.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You tend to remember the overall impression or meaning of an experience rather than the specific details.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You prefer to work through problems step-by-step in a logical sequence rather than jumping around.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You often arrive at answers or insights through a sudden intuition rather than a step-by-step logical process.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 5 — Routine vs Innovation
    {"text": "When approaching a familiar task, you prefer to use the same method that has worked before rather than trying a different approach each time.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You quickly become bored by routine tasks and are always looking for new ways to do things.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When forming an opinion or making a point, you rely more on verified facts and specific examples than on general patterns and gut-level insight.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You enjoy exploring imaginative, hypothetical scenarios — including ones that may never actually happen.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When making plans, you stick to what is realistic and achievable rather than what is ideally possible.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are drawn to big visions and ideals, even when they seem difficult or unlikely to achieve.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When solving a problem, you are more drawn to applying what has been shown to work in practice than to exploring untested theoretical frameworks.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are more inspired by abstract concepts, theories, and imaginative ideas than by straightforward facts and concrete details.", "category": "SN", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # ═══════════════════════════════════════════════════════════════════════════
    # T / F  —  Thinking vs Feeling  (23 questions)
    # 5 facets: Decision Basis | Critique Style | Conflict Response |
    #           Empathy | Advising Others
    # A-pole (T): logical, objective, principle-based, critique-comfortable
    # B-pole (F): values-based, empathetic, harmony-seeking, person-centred
    # ═══════════════════════════════════════════════════════════════════════════

    # Facet 1 — Decision Basis
    {"text": "When making an important decision, you rely primarily on logical reasoning and objective analysis.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When making an important decision, your personal values and how it will affect people matter more than pure logic.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You believe that rules and principles should be applied consistently, regardless of individual circumstances or feelings.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You believe that circumstances and people's feelings should influence how rules and standards are applied.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 2 — Critique and Feedback
    {"text": "You find it straightforward to give direct critical feedback to someone when it will help them improve.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When giving feedback, you naturally soften criticism to protect the other person's feelings, even if it makes the message less clear.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When evaluating someone's idea or work, you focus on its logical merits and flaws rather than on how the person feels about it.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When evaluating someone's idea or work, you instinctively consider how your evaluation will affect that person emotionally.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 3 — Conflict and Debate
    {"text": "You genuinely enjoy a good argument or debate — challenging ideas and being challenged sharpens your thinking.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find interpersonal conflict uncomfortable and naturally try to find ways to restore harmony rather than win an argument.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When someone becomes upset during a discussion, you are able to maintain your position without being deflected by their emotions.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When someone shares how deeply something affects them, it significantly influences how you think about the issue.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 4 — Empathy and Emotional Awareness
    {"text": "You are able to analyse a situation involving people's feelings without being emotionally affected by it yourself.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are highly sensitive to other people's emotional states and can often sense when someone is upset even before they say so.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When someone is wrong, you can disagree with their view firmly without it affecting your feelings toward them personally.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Maintaining warmth and positive relationships in a group is very important to you, sometimes more than reaching the right answer.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 5 — Advising Others and Priorities
    {"text": "When a friend comes to you with a problem, your natural response is to analyse the situation and suggest a practical solution.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When a friend comes to you with a problem, your first instinct is to listen, empathise, and make them feel understood.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "In a team setting, getting the best outcome is more important to you than making sure everyone feels comfortable.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "In a team setting, ensuring everyone feels included and valued is as important to you as achieving the best outcome.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "If a group consensus is logically wrong, you will say so even if it makes you unpopular.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find it difficult to strongly oppose a group decision even when you privately disagree, because you value the group's unity.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When someone has done something wrong, you think it is more important that the correct consequences follow than that the person feels forgiven.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},

    {"text": "When you sense that someone is hurting, your first instinct is to acknowledge and sit with their feelings rather than immediately trying to find a solution.", "category": "TF", "dimension_a_weight": 1, "dimension_b_weight": 1},
    # ═══════════════════════════════════════════════════════════════════════════
    # J / P  —  Judging vs Perceiving  (23 questions)
    # 5 facets: Structure/Organisation | Closure | Planning | Adaptability |
    #           Process vs Goal
    # A-pole (J): organised, decisive, closure-seeking, planned, structured
    # B-pole (P): flexible, open-ended, spontaneous, adaptable, process-oriented
    # ═══════════════════════════════════════════════════════════════════════════

    # Facet 1 — Structure and Organisation
    {"text": "You keep your workspace and study materials organised so that you can find everything quickly.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are comfortable with a degree of clutter and informality in your workspace — you know where things are, even if others do not.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You feel more productive and less stressed when you have a clear daily schedule or routine to follow.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Rigid schedules feel constraining to you — you prefer the freedom to decide how to spend your time as the day unfolds.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 2 — Closure and Decisiveness
    {"text": "Once you have made a decision, you feel relieved and ready to move forward rather than continuing to weigh your options.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Even after making a decision, you often continue to think about whether there might be a better option you have not considered.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "Leaving important questions or plans unresolved for a long time makes you anxious or unsettled.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are comfortable leaving plans open and flexible for a long time, rather than pinning things down before necessary.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 3 — Planning Behaviour
    {"text": "Before a trip, event, or project, you prefer to plan everything out in advance rather than figuring things out as you go.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You enjoy the excitement of doing things spontaneously, without a detailed plan, and adapting as things unfold.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When you have an assignment or deadline, you typically start well in advance so you are never rushing at the last minute.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You often do your best work close to a deadline, when the pressure helps you focus and the direction has become clearer.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 4 — Adaptability vs Control
    {"text": "You prefer environments where expectations are clear and things go according to plan.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "When plans change unexpectedly, you adapt easily and often find the change more interesting than the original plan.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You feel uncomfortable relaxing or doing something enjoyable when you know you have an unfinished task waiting.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You find it easy to mix enjoyment and work fluidly, switching between them based on what feels right at the time.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},

    # Facet 5 — Process vs Goal Focus
    {"text": "When working on a project, you are more motivated by reaching the final outcome and completing it than by the exploration and discovery along the way.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You often find the process of exploring and discovering more interesting than actually finishing and closing off a project.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You regularly make to-do lists, set goals in writing, and track your progress toward them.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You prefer to keep your plans loosely in your head rather than writing them out in rigid lists or timelines.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You believe in following established rules and procedures, even when breaking them slightly might seem more convenient.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are comfortable bending rules or procedures when the situation genuinely calls for a more flexible approach.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You prefer to be thoroughly prepared and certain before starting something, rather than starting and adjusting along the way.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
    {"text": "You are energised by open-ended situations where the path forward is not yet decided, because you enjoy responding to what unfolds rather than following a fixed plan.", "category": "JP", "dimension_a_weight": 1, "dimension_b_weight": 1},
]
# A-pole questions lean positive (strongly agree = +3 → A-pole)
# B-pole questions lean positive (strongly agree = +3 → B-pole, i.e. value = -3 scored)
# Odd index (0,2,4…) → A-pole question; even index (1,3,5…) → B-pole question
# For B-pole questions we flip the answer VALUE sign during scoring in services.py
# Here we encode the pole into dimension_a_weight / dimension_b_weight:
# A-pole questions: dimension_a_weight=1, dimension_b_weight=0
# B-pole questions: dimension_a_weight=0, dimension_b_weight=1
# ... see services.py for how values are combined.

ANSWER_CHOICES = [
    {"text": "Strongly Agree",    "value": 3},
    {"text": "Agree",             "value": 2},
    {"text": "Slightly Agree",    "value": 1},
    {"text": "Neutral",           "value": 0},
    {"text": "Slightly Disagree", "value": -1},
    {"text": "Disagree",          "value": -2},
    {"text": "Strongly Disagree", "value": -3},
]

DIMENSIONS = [
    {"code": "EI", "dimension_a": "Extraversion", "dimension_b": "Introversion",
     "description": "This dimension measures where you get your energy. Extraverts (E) are energised by interacting with people and the outer world. Introverts (I) are energised by spending time in their inner world of ideas and reflections."},
    {"code": "SN", "dimension_a": "Sensing", "dimension_b": "Intuition",
     "description": "This dimension measures how you take in information. Sensing (S) types focus on concrete facts and direct experience. Intuitive (N) types focus on patterns, possibilities, and the big picture."},
    {"code": "TF", "dimension_a": "Thinking", "dimension_b": "Feeling",
     "description": "This dimension measures how you make decisions. Thinking (T) types use logical analysis and objective criteria. Feeling (F) types consider people's values and how decisions affect others."},
    {"code": "JP", "dimension_a": "Judging", "dimension_b": "Perceiving",
     "description": "This dimension measures how you approach the outside world. Judging (J) types prefer structure, closure, and planned living. Perceiving (P) types prefer flexibility, spontaneity, and keeping options open."},
]


class Command(BaseCommand):
    help = "Load comprehensive, balanced MBTI data (questions, types, dimensions)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing MBTI data before loading",
        )

    def handle(self, *args, **options):
        # ── Safe reload: never delete PersonalityType or Questions by default ──
        # Deleting PersonalityType would cascade to AssessmentResult, wiping every
        # student result in the database.  Deleting Questions cascades to
        # QuestionResponse, losing all student answers.
        #
        # Default (safe) mode: update-or-create personality types and dimensions;
        # wipe only AnswerChoice (no student data there) then rebuild questions
        # by matching (text, category) so duplicates never accumulate.
        #
        # Use --clear only on a fresh install with no student data yet.
        if options.get("clear"):
            self.stdout.write(self.style.WARNING(
                "--clear: wiping ALL MBTI data including student results!"
            ))
            AnswerChoice.objects.all().delete()
            Question.objects.all().delete()
            PersonalityType.objects.all().delete()
            MBTIDimension.objects.all().delete()
        else:
            # Safe path: clear only AnswerChoices, leave student data intact
            AnswerChoice.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(
                "Loading MBTI data (safe mode — student results are preserved)..."
            ))

        with transaction.atomic():
            self._load_dimensions()
            self._load_personality_types()
            self._load_questions()

        self.stdout.write(self.style.SUCCESS("\n✅ MBTI data loaded successfully!"))
        self.stdout.write(f"   Dimensions:        {MBTIDimension.objects.count()}")
        self.stdout.write(f"   Personality types: {PersonalityType.objects.count()}")
        self.stdout.write(f"   Questions:         {Question.objects.count()}")
        self.stdout.write(f"   Answer choices:    {AnswerChoice.objects.count()}")


    def _load_dimensions(self):
        for d in DIMENSIONS:
            obj, created = MBTIDimension.objects.update_or_create(
                code=d["code"],
                defaults={
                    "dimension_a": d["dimension_a"],
                    "dimension_b": d["dimension_b"],
                    "description": d["description"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} dimension: {obj}")

    def _load_personality_types(self):
        for pt in PERSONALITY_TYPES:
            obj, created = PersonalityType.objects.update_or_create(
                mbti_type=pt["mbti_type"],
                defaults={
                    "name": pt["name"],
                    "description": pt["description"],
                    "strengths": pt["strengths"],
                    "weaknesses": pt["weaknesses"],
                    "career_recommendations": pt["career_recommendations"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} type: {obj}")

    def _load_questions(self):
        # Group questions by category into pairs: odd=A-pole, even=B-pole
        by_cat = {"EI": [], "SN": [], "TF": [], "JP": []}
        for q in QUESTIONS:
            by_cat[q["category"]].append(q)

        new_q = 0
        rebuilt_choices = 0
        for cat, qs in by_cat.items():
            for idx, q_data in enumerate(qs):
                is_a_pole = (idx % 2 == 0)
                a_w = 1 if is_a_pole else 0
                b_w = 0 if is_a_pole else 1

                question, created = Question.objects.update_or_create(
                    text=q_data["text"],
                    defaults={
                        "category": cat,
                        "dimension_a_weight": a_w,
                        "dimension_b_weight": b_w,
                    },
                )

                # Always (re)create AnswerChoices — they were wiped at the start
                # of handle() so the question always needs fresh choices regardless
                # of whether the question record is new or pre-existing.
                for ac in ANSWER_CHOICES:
                    value = ac["value"] if is_a_pole else -ac["value"]
                    AnswerChoice.objects.create(
                        question=question,
                        text=ac["text"],
                        value=value,
                    )
                rebuilt_choices += 1
                if created:
                    new_q += 1

        self.stdout.write(
            f"  Questions: {new_q} new, {rebuilt_choices - new_q} updated. "
            f"Answer choices rebuilt for all {rebuilt_choices} questions."
        )

