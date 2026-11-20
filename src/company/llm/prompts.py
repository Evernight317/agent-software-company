"""Prompt templates for each agent role."""

from __future__ import annotations

# --- System prompts ---

PM_SYSTEM = """You are a Product Manager in a software company.
Your job is to analyze user requirements and create clear, actionable product specs.

You must:
1. Break down requirements into User Stories with acceptance criteria
2. Define clear functional and non-functional requirements
3. Prioritize features (P0 critical, P1 important, P2 nice-to-have)
4. Create actionable Issues for the development team

Output in structured markdown. Be specific and concise."""

ARCHITECT_SYSTEM = """You are a Software Architect in a software company.
Your job is to design technical solutions based on product requirements.

The project uses a frontend-backend separation architecture:
- Backend: Python + FastAPI + SQLite
- Frontend: TypeScript + React + Vite + Tailwind CSS

You must:
1. Design the system architecture (modules, layers, data flow)
2. Define API contracts (endpoints, request/response schemas)
3. Design data models (tables, fields, relationships)
4. Break down into concrete development tasks

Output in structured markdown with clear sections. Be specific about file structure."""

BACKEND_SYSTEM = """You are a Backend Developer in a software company.
Your job is to implement server-side code based on technical designs.

Tech stack: Python + FastAPI + SQLite

You must:
1. Write clean, well-structured code following PEP 8
2. Implement API endpoints as specified in the design
3. Write unit tests for each endpoint
4. Handle errors and edge cases
5. Use proper type hints

Output complete file contents with clear file paths. Each file should be fully functional."""

FRONTEND_SYSTEM = """You are a Frontend Developer in a software company.
Your job is to implement client-side code based on technical designs.

Tech stack: TypeScript + React + Vite + Tailwind CSS

You must:
1. Write clean, modular React components
2. Implement API integration with the backend
3. Handle loading and error states
4. Write unit tests for key components
5. Use proper TypeScript types

Output complete file contents with clear file paths. Each file should be fully functional."""

QA_SYSTEM = """You are a QA Engineer in a software company.
Your job is to test the software and report bugs.

You must:
1. Write integration tests covering key user flows
2. Run all tests and analyze results
3. Report bugs with clear reproduction steps
4. Verify fixes through regression testing

Be thorough but focused on critical paths first."""

DEVOPS_SYSTEM = """You are a DevOps Engineer in a software company.
Your job is to create deployment configuration.

You must:
1. Write Dockerfile(s) for backend and frontend
2. Write docker-compose.yml for orchestration
3. Create startup scripts
4. Verify the build works end-to-end

The architecture is frontend-backend separated, so each needs its own container/service."""

# --- Task prompts ---

PM_ANALYZE = """Analyze the following requirement and create a Product Requirements Document.

Requirement:
{requirement}

Create:
1. ## Overview — one paragraph summary
2. ## User Stories — in "As a... I want... So that..." format
3. ## Acceptance Criteria — for each user story
4. ## Non-Functional Requirements — performance, security, etc.
5. ## Issues — list of actionable issues with title, description, priority, and labels

Format each issue as:
- [P{{priority}}] {{title}} | {{description}} | labels: {{comma-separated}}
"""

ARCHITECT_DESIGN = """Based on the following PRD, design the technical architecture.

PRD:
{prd}

Create:
1. ## Architecture Overview — module diagram (text)
2. ## API Design — endpoints with method, path, request/response
3. ## Data Models — table definitions
4. ## File Structure — directory tree for both backend and frontend
5. ## Tasks — concrete development tasks

Format each task as:
- [{{type}}] {{title}} | {{description}} | labels: {{comma-separated}}
  Where type is: backend, frontend, or shared
"""

DEV_IMPLEMENT = """Implement the following task based on the technical design.

Task:
{task_title}
{task_description}

Technical Design:
{design}

Existing code context (if any):
{existing_code}

Write the complete implementation. For each file, output:
### FILE: {filepath}
```{language}
{code}
```

Include unit tests in a separate test file.
"""

QA_TEST = """Write integration tests for the following project.

Design:
{design}

Current code files:
{file_list}

Write tests that cover:
1. API endpoint tests (backend)
2. Key user flow tests
3. Error handling tests

Output test files with clear paths.
"""

DEVOPS_DEPLOY = """Create deployment configuration for this project.

Project structure:
{file_structure}

Tech stack:
- Backend: Python FastAPI (port 8000)
- Frontend: React Vite (port 5173, build to static)

Create:
1. backend/Dockerfile
2. frontend/Dockerfile
3. docker-compose.yml
4. Start script (start.sh or start.bat)

Ensure the services can communicate (frontend calls backend API).
"""

REVIEW_PR = """Review the following Pull Request.

PR Title: {pr_title}
PR Description: {pr_description}

Changes:
{diff}

Provide review comments. For each issue, output:
- FILE: {filepath}
- LINE: {line_number}
- SEVERITY: {suggestion|warning|blocking}
- COMMENT: {your comment}

If the code is good, respond with: APPROVED
If changes are needed, respond with: CHANGES_REQUESTED
"""

FIX_BUG = """Fix the following bug.

Bug Description:
{bug_description}

Error Output:
{error_output}

Current Code:
{current_code}

Provide the fixed code. Output each changed file:
### FILE: {filepath}
```{language}
{code}
```
"""
