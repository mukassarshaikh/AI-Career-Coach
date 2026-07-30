"""
llm_service.py — Shared Groq API client wrapper.

All LLM inference calls across the application MUST go through this service.
- All prompts are templated and versioned in this module.
- Retries with exponential backoff on Groq rate limits (429).
- Every call writes an audit log to `ai_generation_logs` per BRD requirement.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from groq import AsyncGroq, APIStatusError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.logs import AiGenerationLog

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------
STRUCTURE_RESUME_SYSTEM_PROMPT = """You are an expert resume parsing AI.
Your task is to analyze raw resume text and extract structured information into a clean JSON object.

The JSON response MUST follow this exact schema:
{
  "experience": [
    {
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "YYYY-MM or string",
      "end_date": "YYYY-MM, Present, or string",
      "description": "Brief summary of position",
      "highlights": ["Key responsibility or accomplishment 1", "Key responsibility or accomplishment 2"]
    }
  ],
  "education": [
    {
      "institution": "University/School Name",
      "degree": "Degree Name (e.g. Bachelor of Science)",
      "field_of_study": "Major/Field",
      "graduation_year": "YYYY or string"
    }
  ],
  "skills": {
    "technical": ["Skill 1", "Skill 2"],
    "tools": ["Tool 1", "Tool 2"],
    "soft_skills": ["Skill 1", "Skill 2"]
  },
  "achievements": [
    "Key award, certification, or key project accomplishment 1"
  ]
}

Return ONLY valid, minified JSON adhering strictly to this schema. Do not include markdown headers or commentary outside the JSON.
"""

STRUCTURE_RESUME_USER_PROMPT_TEMPLATE = """Extract structured data from the following resume text:

--- BEGIN RESUME TEXT ---
{resume_text}
--- END RESUME TEXT ---
"""

SCORE_RESUME_ATS_SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) evaluation AI.
Your job is to analyze a candidate's resume and calculate an ATS compatibility score along with sub-scores.

The JSON response MUST follow this exact schema:
{
  "overall_score": 85,
  "formatting": 90,
  "structure": 80,
  "parseability": 85,
  "feedback": [
    "Clear section headers detected.",
    "Good formatting and parseable font choice.",
    "Consider replacing complex tables with plain bullet points."
  ]
}

Return ONLY valid JSON matching this schema. All score values must be integers between 0 and 100.
"""

SCORE_RESUME_ATS_USER_PROMPT_TEMPLATE = """Evaluate the following resume for ATS parseability, formatting, and structural quality:

--- PARSED RESUME DATA ---
{parsed_json}

--- RAW RESUME TEXT ---
{raw_text}
"""

AUDIT_RESUME_GRAMMAR_SYSTEM_PROMPT = """You are a professional resume editor and grammar auditor AI.
Your job is to audit raw resume text for grammar, spelling, clarity, tone, and active voice.

The JSON response MUST follow this exact schema:
{
  "suggestions": [
    {
      "location": "Experience - Senior Software Engineer at Tech Corp",
      "issue": "Use of weak passive phrasing ('was responsible for leading')",
      "suggestion": "Led a team of 6 engineers..."
    }
  ]
}

Return ONLY valid JSON matching this schema. If no grammar issues are found, return {"suggestions": []}.
"""

AUDIT_RESUME_GRAMMAR_USER_PROMPT_TEMPLATE = """Audit the following resume text for grammar, tone, active voice, and conciseness:

--- RAW RESUME TEXT ---
{raw_text}
"""

ANALYZE_KEYWORDS_SYSTEM_PROMPT = """You are an expert ATS keyword analyzer and technical recruiter AI.
Your job is to compare a candidate's resume text against a target job description to identify matched keywords, missing keywords, and prioritized action items.

The JSON response MUST follow this exact schema:
{
  "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
  "missing_keywords": [
    {
      "keyword": "Docker",
      "importance": "high",
      "category": "technical",
      "reason": "Explicitly required for deployment in the job description"
    },
    {
      "keyword": "Kubernetes",
      "importance": "medium",
      "category": "technical",
      "reason": "Listed as a preferred qualification"
    }
  ],
  "action_items": [
    {
      "priority": 1,
      "section": "Skills",
      "action": "Add Docker containerization experience to skills section",
      "impact": "Fills critical missing keyword gap"
    }
  ]
}

Return ONLY valid JSON adhering strictly to this schema.
"""

ANALYZE_KEYWORDS_USER_PROMPT_TEMPLATE = """Compare the following resume text against the target job description:

--- CANDIDATE RESUME TEXT ---
{resume_text}

--- TARGET JOB DESCRIPTION ---
{jd_text}
"""


def _get_groq_client() -> AsyncGroq:
    """Returns an AsyncGroq client initialized with the configured API key."""
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY is not set in environment settings.")
    return AsyncGroq(api_key=settings.groq_api_key or "dummy_key")


async def log_ai_generation(
    module: str,
    prompt: str,
    response: str,
    model_used: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
) -> None:
    """
    Logs an AI prompt and response to `ai_generation_logs` table for auditability.
    """
    if db is None:
        return

    try:
        log_entry = AiGenerationLog(
            user_id=user_id,
            module=module,
            prompt=prompt[:5000],  # Truncate if exceedingly long to save space
            response=response[:10000],
            model_used=model_used,
        )
        db.add(log_entry)
        await db.commit()
    except Exception as exc:
        logger.error(f"Failed to save AI generation log: {exc}")
        await db.rollback()


async def _call_groq_with_retry(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3,
) -> str:
    """
    Helper function to call Groq completions API with backoff retry on 429 rate limits.
    """
    client = _get_groq_client()
    attempt = 0
    backoff_delay = 1.0

    while attempt < max_retries:
        try:
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=settings.groq_model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return chat_completion.choices[0].message.content or "{}"
        except (RateLimitError, APIStatusError) as err:
            status_code = getattr(err, "status_code", 500)
            if status_code == 429 and attempt < max_retries - 1:
                logger.warning(
                    f"Groq API rate limited (429). Retrying in {backoff_delay}s... (Attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(backoff_delay)
                backoff_delay *= 2.0
                attempt += 1
            else:
                logger.error(f"Groq API error (status {status_code}): {err}")
                raise err
        except Exception as exc:
            logger.error(f"Unexpected error calling Groq API: {exc}")
            raise exc

    return "{}"


async def structure_resume(
    text: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calls Groq LLM to convert raw resume text into a structured JSON dict
    matching FR-1.1 schema (experience, education, skills, achievements).
    """
    user_prompt = STRUCTURE_RESUME_USER_PROMPT_TEMPLATE.format(resume_text=text)
    full_prompt = f"{STRUCTURE_RESUME_SYSTEM_PROMPT}\n\n{user_prompt}"

    response_text = await _call_groq_with_retry(
        system_prompt=STRUCTURE_RESUME_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_retries=max_retries,
    )

    await log_ai_generation(
        module="resume",
        prompt=full_prompt,
        response=response_text,
        model_used=settings.groq_model,
        user_id=user_id,
        db=db,
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {response_text}")
        return {
            "experience": [],
            "education": [],
            "skills": {"technical": [], "tools": [], "soft_skills": []},
            "achievements": [],
            "raw_fallback": response_text,
        }


async def score_resume_ats(
    parsed_json: Dict[str, Any],
    raw_text: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calls Groq LLM to evaluate ATS compatibility (overall_score, formatting, structure, parseability, feedback).
    Logs AI generation to `ai_generation_logs`.
    """
    user_prompt = SCORE_RESUME_ATS_USER_PROMPT_TEMPLATE.format(
        parsed_json=json.dumps(parsed_json, indent=2),
        raw_text=raw_text or "",
    )
    full_prompt = f"{SCORE_RESUME_ATS_SYSTEM_PROMPT}\n\n{user_prompt}"

    response_text = await _call_groq_with_retry(
        system_prompt=SCORE_RESUME_ATS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_retries=max_retries,
    )

    await log_ai_generation(
        module="resume",
        prompt=full_prompt,
        response=response_text,
        model_used=settings.groq_model,
        user_id=user_id,
        db=db,
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse ATS score response: {response_text}")
        return {
            "overall_score": 70,
            "formatting": 70,
            "structure": 70,
            "parseability": 70,
            "feedback": ["Failed to parse detailed ATS breakdown from LLM."],
        }


async def audit_resume_grammar(
    raw_text: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calls Groq LLM to audit raw resume text for grammar, spelling, clarity, and tone.
    Logs AI generation to `ai_generation_logs`.
    """
    user_prompt = AUDIT_RESUME_GRAMMAR_USER_PROMPT_TEMPLATE.format(raw_text=raw_text or "")
    full_prompt = f"{AUDIT_RESUME_GRAMMAR_SYSTEM_PROMPT}\n\n{user_prompt}"

    response_text = await _call_groq_with_retry(
        system_prompt=AUDIT_RESUME_GRAMMAR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_retries=max_retries,
    )

    await log_ai_generation(
        module="resume",
        prompt=full_prompt,
        response=response_text,
        model_used=settings.groq_model,
        user_id=user_id,
        db=db,
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse grammar audit response: {response_text}")
        return {"suggestions": []}


async def analyze_keywords_llm(
    resume_text: str,
    jd_text: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Calls Groq LLM to compare raw resume text against a target job description text.
    Extracts matched keywords, missing keywords, and prioritized action items.
    Logs AI generation to `ai_generation_logs`.
    """
    user_prompt = ANALYZE_KEYWORDS_USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text or "",
        jd_text=jd_text or "",
    )
    full_prompt = f"{ANALYZE_KEYWORDS_SYSTEM_PROMPT}\n\n{user_prompt}"

    response_text = await _call_groq_with_retry(
        system_prompt=ANALYZE_KEYWORDS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_retries=max_retries,
    )

    await log_ai_generation(
        module="resume",
        prompt=full_prompt,
        response=response_text,
        model_used=settings.groq_model,
        user_id=user_id,
        db=db,
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse keyword analysis JSON response: {response_text}")
        return {
            "matched_keywords": [],
            "missing_keywords": [],
            "action_items": [],
        }
