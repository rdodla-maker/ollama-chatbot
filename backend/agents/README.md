# Agent Scaffolds for Stage 2 Automation

This directory contains **placeholder agent implementations** for future Stage 2 automation features. These are intentionally kept as scaffolds to establish the architecture for upcoming functionality.

## Current Agents

### 📧 **EmailAgent** (`email_agent.py`)
**Status:** Placeholder (NotImplementedError)  
**Purpose:** Cold email campaign automation  
**Stage 2 Features:**
- Draft personalized outreach emails
- Follow-up sequence automation
- Email template management
- Response tracking integration

### 💼 **JobAgent** (`job_agent.py`)
**Status:** Placeholder (NotImplementedError)  
**Purpose:** Automated job discovery  
**Stage 2 Features:**
- Scrape job boards (LinkedIn, Indeed, etc.)
- Match jobs to candidate profiles
- Auto-apply to matching positions
- Track application status across platforms

### 📄 **ResumeAgent** (`resume_agent.py`)
**Status:** Placeholder (NotImplementedError)  
**Purpose:** Dynamic resume customization  
**Stage 2 Features:**
- Analyze resume for improvements
- Generate tailored versions per job
- A/B test resume variations
- Track resume performance metrics

## Architecture Notes

These agents are designed to integrate with:
- **Workflow Engine:** For orchestrating multi-step automation
- **Event Bus:** For cross-service communication
- **Task Queue:** For background job processing
- **Candidate Memory:** For personalization
- **Integration Seams:** For external service connections (n8n, APIs)

## When to Implement

Implement these agents during **Stage 2** when:
1. Core application flow is stable
2. User feedback validates automation needs
3. Infrastructure is battle-tested in production
4. Product-market fit is confirmed

## Do Not Remove

These scaffolds are **intentional placeholders** for future automation. Removing them would require recreating the architecture later. Keep them as reference for Stage 2 development.
