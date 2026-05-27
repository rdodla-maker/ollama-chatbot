"""Generate core job-application artifacts using Ollama."""

import asyncio

from models.schemas import GenerateApplicationRequest
from services.ollama_service import generate_completion


def build_email_prompt(payload: GenerateApplicationRequest) -> str:
    return f"""You are an assistant helping a job seeker draft a concise outreach email.

Company: {payload.company}
Role: {payload.role}
Tone: {payload.tone}
Key skills: {payload.skills}
Resume:
{payload.resume_text}

Job description:
{payload.job_description}

Write a personalized professional email.
Keep it practical and specific to the role.
Output email text only.
"""


def build_cover_letter_prompt(payload: GenerateApplicationRequest) -> str:
    return f"""You are an assistant helping a candidate generate a tailored cover letter.

Company: {payload.company}
Role: {payload.role}
Tone: {payload.tone}
Skills: {payload.skills}
Resume:
{payload.resume_text}

Job description:
{payload.job_description}

Write a cover letter tailored to the role.
Keep it realistic, professional, and under 450 words.
Output cover letter text only.
"""


def build_resume_suggestions_prompt(payload: GenerateApplicationRequest) -> str:
    return f"""You are a resume reviewer.

Target company: {payload.company}
Target role: {payload.role}
Skills: {payload.skills}

Resume:
{payload.resume_text}

Job description:
{payload.job_description}

Give practical resume improvement suggestions.
Use short bullet points grouped by impact.
Output plain text only.
"""


async def generate_application_materials(payload: GenerateApplicationRequest) -> dict[str, str]:
    email_prompt = build_email_prompt(payload)
    cover_prompt = build_cover_letter_prompt(payload)
    resume_prompt = build_resume_suggestions_prompt(payload)

    generated_email, generated_cover_letter, resume_suggestions = await asyncio.gather(
        generate_completion(email_prompt),
        generate_completion(cover_prompt),
        generate_completion(resume_prompt),
    )

    return {
        "generated_email": generated_email.strip(),
        "generated_cover_letter": generated_cover_letter.strip(),
        "resume_suggestions": resume_suggestions.strip(),
    }