PRODUCTION DEPLOYMENT MASTER PLAYBOOK
A Universal, Reusable Deployment & DevOps Playbook for Full-Stack Software Projects

Paste this document into any future project as a standing reference for an AI coding assistant (Claude Code, Cursor, Codex, Gemini CLI, etc.) or a human engineer. It governs how the project gets deployed, secured, monitored, and scaled — never how the application looks or behaves.

Table of Contents
1. Introduction
2. Production Deployment Philosophy
3. Project Structure
4. Environment Variables
5. Cloud Native Deployment
6. Docker Deployment
7. Database Best Practices
8. Object Storage
9. Redis
10. Background Workers
11. Security
12. Logging
13. Monitoring
14. Performance
15. CI/CD
16. README Template
17. Deployment Architecture Diagrams
18. Interview Talking Points
19. Production Checklist
20. Common Deployment Mistakes
21. Troubleshooting Guide
22. Scaling Strategy

================================================================================
1. Introduction
================================================================================
1.1 What this document is
This playbook is a deployment operating manual, not a design document. It exists to answer one question, repeatedly, across every project you ever ship: "How do I take working application code and make it run safely, reliably, and cheaply in production — without touching what the application does?"

1.2 What this document is not
This is not a UI/UX guide, a system design document for business logic, or a one-time deployment log. If a task involves changing what a button does, how a page looks, or how a feature behaves, that task does not belong in this playbook.

1.3 Who should use this
AI coding assistants, solo developers, and teams building production-grade software projects without dedicated SRE hires.

1.4 How to use this document
Follow Section 1.5 Critical Preservation Rules. Select Cloud Native (Ch 5) or Docker (Ch 6) or both, and implement concerns incrementally.

1.5 Critical Preservation Rules (Read First)
The deployed application must look, feel, and behave exactly as it did before deployment work began.
An engineer or AI assistant working from this playbook may only touch deployment, infrastructure, security, performance, scalability, reliability, monitoring, logging, CI/CD, and documentation. It may never touch UI, UX, layout, styling, branding, routing, or feature set.

1.6 Applicability - What to Include vs. Skip
Chapter 1-4: Always Required.
Chapter 5-6: Conditional (Cloud Native vs Docker).
Chapter 7: Database (Always Required).
Chapter 8-10: Storage, Redis, Workers (Conditional).
Chapter 11-13: Security, Logging, Monitoring (Always Required).
Chapter 14-16: Performance, CI/CD, README (Always Required).
Chapter 17-22: Diagrams, Interview Points, Checklist, Troubleshooting, Scaling (Reference).

================================================================================
2. Production Deployment Philosophy
================================================================================
2.1 Deployment is a separate concern from development.
2.2 Boring technology first.
2.3 Twelve-Factor as a baseline.
2.4 Everything reproducible, nothing tribal.
2.5 Fail loud, fail early.
2.6 Security and observability are first-class.
2.7 Two architectures, one codebase (Cloud Native & Docker).

================================================================================
3. Project Structure
================================================================================
Deployment artifacts live in clearly separated, predictable locations, distinct from application source (e.g. Dockerfiles, render.yaml, vercel.json, infra/).

================================================================================
4. Environment Variables
================================================================================
4.1 Nothing environment-specific is hardcoded.
4.2 Naming conventions: SCREAMING_SNAKE_CASE.
4.3 .env (gitignored), .env.example (committed).
4.4 Validation at process boot.
4.5 Secrets management by platform.

================================================================================
5. Cloud Native Deployment
================================================================================
5.1 Frontend -> Vercel (or static host).
5.2 Backend -> Render / Railway.
5.3 Database -> Managed Vector DB / Postgres (Pinecone / Neon / Supabase).
5.4 DNS & HTTPS: Automated Let's Encrypt certificates.

================================================================================
6. Docker Deployment
================================================================================
6.1 Standalone containerized stack with Dockerfile & docker-compose.yml.
6.2 Multi-stage builds, non-root users, layer caching.
6.3 Isolated bridge networks (`app-network`).
6.4 Healthchecks and volume persistence.

================================================================================
7. Database Best Practices
================================================================================
7.1 Connection pooling & statelss memory management.
7.2 Version-controlled migrations / reproducible seed documents.
7.3 Automated backups and verified restore procedures.
7.4 Indexes on foreign keys and frequently queried fields.

================================================================================
8. Object Storage & 9. Redis & 10. Background Workers
================================================================================
Decouple slow, blocking, or heavy operations from synchronous HTTP response cycles.

================================================================================
11. Security & 12. Logging & 13. Monitoring
================================================================================
11.1 Security Headers (Helmet/CORS).
11.2 Rate limiting and parameterization.
12.1 Structured JSON logs with request correlation IDs.
13.1 Health endpoints (`/health` liveness, `/ready` readiness).
13.2 Observability & error tracing (Langfuse / Sentry).

================================================================================
14. Performance & 15. CI/CD & 16. README Template
================================================================================
Compression, caching headers, automated GitHub Actions CI/CD workflows, and comprehensive deployment README documentation.

================================================================================
19. Production Checklist & 20. Mistakes & 21. Troubleshooting & 22. Scaling
================================================================================
Pre-flight verification gate, troubleshooting guides for common deployment issues, and stage-by-stage scaling strategy from Portfolio to Enterprise.
