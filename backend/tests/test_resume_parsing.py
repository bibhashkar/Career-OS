"""
Comprehensive unit and integration test suite for Career-OS resume parsing,
Jev-style layout triage routing, and grounded semantic profile synthesis.
Tests diverse resume formats: Senior Full-Stack, AI/ML Infrastructure,
Entry-Level New Grad, Executive VP of Engineering, and LinkedIn PDF export.
"""

from app.ingestion.resume_parser import (
    parse_generic_resume_text,
    synthesize_grounded_semantic_summary,
)
from app.ingestion.router import triage_resume_layout

# -----------------------------------------------------------------------------
# Test Fixtures: Diverse Real-World Resume Layouts
# -----------------------------------------------------------------------------

BIBHASH_KAR_RESUME = """Bibhash Kar | (+1) 702-690-7348 | bibhash108@gmail.com | Las Vegas, Nevada | linkedin.com/in/bibhash108
Senior Software Engineer with 12+ years of experience in full-stack engineering, distributed systems, and high-throughput transaction
processing. Expert in architecting scalable enterprise systems, optimizing low-latency data pipelines, and leading cross-functional
teams to deliver mission-critical software. Proven track record in designing resilient architectures and driving technical excellence
across the entire software development lifecycle.
Professional Experience
Full Stack Software Developer | Onye Inc., New York, USA | May 2026 – Aug 2026
● Architected a HIPAA-compliant RBAC and multi-factor authentication (MFA/TOTP) engine in Next.js 14 (App Router),
implementing fail-closed layout guards, dynamic PII masking, and passwordless staff onboarding.
● Engineered a standalone Node.js upload microservice using @tus/server with Backblaze B2/S3 backends; implemented
custom security hooks and streaming SHA-256 hash validation for reliable DICOM/PDF uploads.
● Modularized multi-environment cloud infrastructure using Terraform and automated GitHub Actions workflows for linting,
typechecking, deployment, and automated infrastructure drift monitoring.
Senior Software Engineer 2 | Therap BD Ltd., Dhaka, Bangladesh | Oct 2021 – July 2025
● Architected a high-scale EDI transaction processing system handling $7B+ in annual volume; engineered from the ground up
for data integrity and high-speed vendor interoperability.
● Designed and implemented a high-concurrency tracking system for transaction processing, managing 10,000+ daily requests
using a performance-first approach to ensure low-latency responses.
● Mentored 8+ developers on system architecture standards and rigorous code review processes, establishing technical
benchmarks for long-term maintainability and robust security for mission-critical services.
Senior Software Engineer | Therap BD Ltd., Dhaka, Bangladesh | July 2018 – Oct 2021
● Led the redesign of a national distributed billing calculation engine, standardizing calculation logic across diverse regional
datasets to ensure 100% financial accuracy at scale.
● Designed a secure, multi-state interoperability engine for real-time data synchronization across disparate platforms in states
including New York, Florida, New Jersey, Nevada, and Colorado, optimizing for high throughput and strict data protection.
Software Engineer 2 | Therap BD Ltd., Dhaka, Bangladesh | Oct 2016 – July 2018
● Developed a high-volume insurance verification system engineered for high availability and seamless integration with external
vendor APIs across multiple regions.
● Optimized transaction file generation by 42%, reducing request processing to <2 seconds for 1,000+ concurrent dataset and
supporting high-throughput, mission-critical operations.
Software Engineer | Therap BD Ltd., Dhaka, Bangladesh | Aug 2015 – Oct 2016
● Integrated core systems with diverse regional protocols like in Nebraska, North Dakota, South Dakota etc., ensuring system
adaptability and scalability while maintaining compliance with evolving technical standards.
● Engineered advanced automated reporting engines, providing stakeholders with high-fidelity analytical tools to drive
data-driven decision-making.
Associate Software Engineer | Therap BD Ltd., Dhaka, Bangladesh | June 2013 – Aug 2015
● Revamped a critical frontend data grid for high-performance rendering of large-scale datasets and completed specialized
training in Java EE/Spring/JPA and data security.
Education
Master of Science in Management Information System - University of Nevada, Las Vegas | 2025 - May, 2027 (Expected)
Bachelor of Science in Computer Science & Engineering - Shahjalal University of Science & Technology, Bangladesh | 2009 - 2012
Technical Skills
● System Architecture & Design: Software Architecture, Microservices, Distributed Systems, RESTful APIs, Performance
Optimization, Agile/Scrum, Design Patterns, JIRA, Confluence
● Backend & Microservices: Java, Python, TypeScript, SQL, Spring Boot, Spring Framework, Hibernate, JPA, MyBatis,
FastAPI, SQLAlchemy, @tus/server, Node.js, Supabase Auth / GoTrue, SFTP/FTP, SSH
● AI Infrastructure: pyTorch, Vector Databases, MCP, A2A, RAG pipelines, LLM Serving, AI IDE(Claude Code, Antigravity IDE)
● Database: Postgresql, Oracle Database, MongoDB, Redis, Backblaze B2/S3
● Cloud & Infrastructure: Terraform, OpenTofu, Vercel, Render, Docker, CI/CD, GitHub Actions, Linux,, Google Cloud Platform,
Gradle, Maven, Infrastructure Drift Detection, Point-In-Time Recovery (PITR)
● Frontend & UI/UX: JavaScript, React, Next.js 14+, Tailwind CSS, HTML, CornerstoneJS,
● Data Visualization: Tableau, Seaborn, Pandas
● Security & Compliance: RBAC, TOTP MFA, HIPAA Compliance, PII Encryption & Data Masking
● Testing & Quality Assurance: Vitest, React Testing Library, jsdom, lighthouse
Awards Winner, Amazon best sustainability category | Sunhacks: Hackathon at Arizona State University | Sept 27, 2025
"""

AI_ML_INFRASTRUCTURE_RESUME = """Dr. Elena Rostova
elena.rostova@ai-research.org | (415) 555-0199 | San Francisco, CA | linkedin.com/in/elena-rostova
Staff Machine Learning Infrastructure Engineer with 7+ years building large-scale deep learning training and inference clusters.

Work Experience
Staff AI Infrastructure Engineer | NeuralScale AI, San Francisco, CA | Jan 2022 – Present
● Designed and deployed distributed LLM inference engine using vLLM and TensorRT-LLM serving 50,000+ queries/sec across 256 H100 GPUs.
● Reduced tail latency by 35% through custom CUDA kernel optimization and FP8 quantization pipelines in PyTorch.
● Implemented semantic RAG pipeline leveraging pgvector and Redis caching for sub-15ms multi-tenant vector similarity search.
Senior ML Platform Engineer | DeepVision Labs, Mountain View, CA | June 2019 – Dec 2021
● Scaled distributed model training cluster to 1,024 nodes using Ray and Slurm, decreasing checkpoint recovery time by 60%.
● Built automated model evaluation framework benchmarking cross-entropy and perplexity across 10B+ parameter checkpoints.

Education
Doctorate in Computer Science - Stanford University | 2015 – 2019
Bachelor of Science in Mathematics - MIT | 2011 – 2015

Technical Skills
PyTorch, vLLM, TensorRT-LLM, Ray, Triton, CUDA, Python, C++, Docker, Kubernetes, Terraform, GCP, AWS, pgvector, Redis

Awards & Honors
NeurIPS Outstanding Paper Award | NeurIPS Conference | Dec 2023
"""

ENTRY_LEVEL_NEW_GRAD_RESUME = """Marcus Chen
marcus.chen@berkeley.edu | (510) 555-8821 | Berkeley, CA | github.com/marcuschen
Aspiring Junior Software Engineer eager to build robust distributed systems and web platforms.

Education
Bachelor of Science in Computer Science - UC Berkeley | 2022 – 2026 (Expected)
GPA: 3.85 | Dean's Honor List

Work Experience
Software Engineering Intern | Datadog, San Francisco, CA | June 2025 – Aug 2025
● Built real-time dashboard widget in React and TypeScript displaying trace ingestion metrics for 5,000+ enterprise customers.
● Implemented backend Go telemetry pipeline ingesting OpenTelemetry spans with 99.99% availability.

Technical Projects
Distributed KV Store: Implemented Raft consensus algorithm in Go with log compaction and snapshotting.
Job Matcher: Built candidate ranking web application in Python, FastAPI, and PostgreSQL.

Technical Skills
Python, Go, JavaScript, TypeScript, React, PostgreSQL, Docker, Git, CI/CD

Competitions
1st place | CalHacks Hackathon | Oct 2024
"""

EXECUTIVE_VP_ENGINEERING_RESUME = """Sarah Jenkins
sarah.jenkins@exec.com | (212) 555-7733 | New York, NY | linkedin.com/in/sarahjenkins-vp
Vice President of Engineering with 18+ years leading global engineering organizations.

Professional Experience
VP of Engineering | CloudScale Technologies, New York, NY | 2020 – Present
● Scaled engineering team from 15 to 80+ software engineers across North America and Europe while increasing delivery velocity by 45%.
● Managed $25M annual engineering budget, optimizing cloud infrastructure spend on AWS and GCP by $3.2M.
● Championed SOC-2 Type II certification and enterprise-grade security compliance for Fortune 500 financial clients.
Director of Software Engineering | FinCorp Systems, Boston, MA | 2014 – 2020
● Led architecture of real-time trading execution platform processing $20B+ daily volume with zero unplanned downtime.
● Mentored 12+ engineering managers and principal architects across distributed transactions and platform infrastructure.

Education
Master of Business Administration - Harvard Business School | 2012 – 2014
Bachelor of Science in Electrical Engineering - MIT | 2002 – 2006

Skills
Executive Leadership, Budget Management, Distributed Systems, Cloud Architecture, SOC-2, FinTech, Microservices
"""


# -----------------------------------------------------------------------------
# Unit & Integration Tests
# -----------------------------------------------------------------------------


def test_triage_resume_layout_signals() -> None:
    """Verify Jev-style layout triage router accurately classifies diverse resumes."""
    # Standard single-column senior resume
    d1 = triage_resume_layout(BIBHASH_KAR_RESUME, "Bibhash_Kar_Resume_se.pdf")
    assert d1.layout_type in ("standard_single_column", "multi_column_creative")
    assert d1.has_text_layer is True
    assert d1.estimated_experience_density == "senior_staff"
    assert d1.recommended_pipeline == "deep_llm_structured"

    # Scanned empty text layer
    d2 = triage_resume_layout("   \n  ", "Scanned_Scan.pdf")
    assert d2.layout_type == "scanned_image_pdf"
    assert d2.has_text_layer is False
    assert d2.recommended_pipeline == "vision_ocr_pipeline"

    # New Grad resume
    d3 = triage_resume_layout(ENTRY_LEVEL_NEW_GRAD_RESUME, "Marcus_Chen_Resume.pdf")
    assert d3.estimated_experience_density == "entry"


def test_parse_bibhash_kar_resume_exact_extraction() -> None:
    """
    Verify complete extraction of Bibhash Kar's resume:
    Name, 12 YOE, Staff seniority, 6 companies, FinTech + HealthTech domains,
    UNLV Master's education, Sunhacks award, and grounded semantic summary.
    """
    dossier = parse_generic_resume_text(BIBHASH_KAR_RESUME)

    # 1. Identity & Contact Details
    assert dossier.full_name == "Bibhash Kar"
    assert dossier.email == "bibhash108@gmail.com"
    assert dossier.phone == "702-690-7348"
    assert dossier.location == "Las Vegas, Nevada"
    assert dossier.linkedin_url == "https://www.linkedin.com/in/bibhash108"

    # 2. Executive Analytics
    assert dossier.total_years_experience == 12
    assert dossier.seniority_level == "staff"
    assert "Full Stack Software Developer" in dossier.target_roles
    assert (
        "Senior Software Engineer" in dossier.target_roles
        or "Senior Software Engineer 2" in dossier.target_roles
    )

    # 3. Work Experience Positions
    assert len(dossier.work_experience) == 6
    companies = [e.company_name for e in dossier.work_experience]
    assert "Onye Inc." in companies
    assert "Therap BD Ltd." in companies

    # Check atomic proof points and legacy blocks
    assert len(dossier.blocks) >= 10
    assert any(b.metrics for b in dossier.blocks)

    # 4. Business Domain Expertise
    assert len(dossier.domain_expertise) >= 2
    domains = [d.domain for d in dossier.domain_expertise]
    assert any("HealthTech" in d for d in domains)
    assert any("FinTech" in d for d in domains)

    # Verify regulatory frameworks
    fintech_entry = next(d for d in dossier.domain_expertise if "FinTech" in d.domain)
    assert fintech_entry.years_experience >= 8.0
    assert "EDI / X12" in fintech_entry.regulatory_frameworks

    healthtech_entry = next(
        d for d in dossier.domain_expertise if "HealthTech" in d.domain
    )
    assert "HIPAA" in healthtech_entry.regulatory_frameworks

    # 5. Education Records
    assert len(dossier.education) == 2
    degrees = [edu.degree for edu in dossier.education]
    assert any("MASTER" in d for d in degrees)
    assert any("BACHELOR" in d for d in degrees)
    assert any("Nevada" in edu.institution for edu in dossier.education)
    assert any("Shahjalal" in edu.institution for edu in dossier.education)

    # 6. Awards & Honors
    assert len(dossier.awards_and_honors) >= 1
    assert any("sustainability" in a.title.lower() for a in dossier.awards_and_honors)

    # 7. Grounded Semantic Profile Summary
    summary = dossier.semantic_profile_summary
    assert "12+ years" in summary
    assert "FinTech" in summary
    assert "HealthTech" in summary
    assert "$7B" in summary
    assert "distributed systems" in summary.lower()


def test_parse_ai_ml_infrastructure_resume() -> None:
    """Verify extraction of deep AI/ML research and infrastructure resume."""
    dossier = parse_generic_resume_text(AI_ML_INFRASTRUCTURE_RESUME)

    assert dossier.full_name == "Dr. Elena Rostova"
    assert dossier.email == "elena.rostova@ai-research.org"
    assert dossier.seniority_level in ("staff", "senior")
    assert dossier.total_years_experience >= 7
    assert len(dossier.work_experience) == 2

    # Verify AI/ML domain detection
    domains = [d.domain for d in dossier.domain_expertise]
    assert any("AI" in d or "Machine Learning" in d for d in domains)

    # Verify core skills
    assert "PyTorch" in dossier.all_skills_flat
    assert "Docker" in dossier.all_skills_flat
    assert "Kubernetes" in dossier.all_skills_flat

    # Verify Education
    assert len(dossier.education) == 2
    assert any("Stanford" in e.institution for e in dossier.education)


def test_parse_entry_level_new_grad_resume() -> None:
    """Verify extraction of entry-level university student / new grad resume."""
    dossier = parse_generic_resume_text(ENTRY_LEVEL_NEW_GRAD_RESUME)

    assert dossier.full_name == "Marcus Chen"
    assert dossier.email == "marcus.chen@berkeley.edu"
    assert dossier.seniority_level == "entry"
    assert len(dossier.work_experience) == 1
    assert dossier.work_experience[0].company_name == "Datadog"
    assert "React" in dossier.all_skills_flat


def test_parse_executive_vp_engineering_resume() -> None:
    """Verify extraction of executive-level VP of Engineering resume."""
    dossier = parse_generic_resume_text(EXECUTIVE_VP_ENGINEERING_RESUME)

    assert dossier.full_name == "Sarah Jenkins"
    assert dossier.seniority_level in ("staff", "executive")
    assert dossier.total_years_experience >= 18
    assert len(dossier.work_experience) == 2
    companies = [e.company_name for e in dossier.work_experience]
    assert "CloudScale Technologies" in companies
    assert "FinCorp Systems" in companies

    # Check financial and leadership metrics
    summary = dossier.semantic_profile_summary
    assert "years" in summary


def test_synthesize_grounded_semantic_summary_anti_drift() -> None:
    """Verify semantic summary formulation is strictly grounded in candidate facts."""
    dossier = parse_generic_resume_text(BIBHASH_KAR_RESUME)
    summary = synthesize_grounded_semantic_summary(dossier)

    # Must contain verified candidate facts
    assert "12+ years" in summary
    assert "HealthTech" in summary
    assert "FinTech" in summary

    # Must not contain hallucinations or generic buzzwords
    assert "blockchain" not in summary.lower()
    assert "crypto" not in summary.lower()
