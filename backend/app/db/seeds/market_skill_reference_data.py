"""
market_skill_reference_data.py — Starter Market Skill Demand Reference Dataset.

DISCLAIMER & DATA SOURCING DECISION:
This dataset is a starter/approximate reference dataset curated for Phase 1 testing and initial skill-gap benchmarking.
It does NOT originate from a live BLS or real-time job-posting labor market feed.
Per Phase 4 project roadmap, this static starter dataset will eventually be replaced by a live ingestion pipeline.
"""

STARTER_SOURCE = "starter dataset - manual curation, not live market data"

STARTER_MARKET_SKILLS = [
    # 1. Frontend Engineer
    {"role_title": "Frontend Engineer", "skill_name": "React", "demand_weight": 0.95},
    {"role_title": "Frontend Engineer", "skill_name": "TypeScript", "demand_weight": 0.92},
    {"role_title": "Frontend Engineer", "skill_name": "JavaScript", "demand_weight": 0.90},
    {"role_title": "Frontend Engineer", "skill_name": "Next.js", "demand_weight": 0.85},
    {"role_title": "Frontend Engineer", "skill_name": "HTML5 / CSS3", "demand_weight": 0.88},
    {"role_title": "Frontend Engineer", "skill_name": "Tailwind CSS", "demand_weight": 0.80},
    {"role_title": "Frontend Engineer", "skill_name": "State Management (Redux/Zustand)", "demand_weight": 0.78},
    {"role_title": "Frontend Engineer", "skill_name": "REST API Integration", "demand_weight": 0.82},
    {"role_title": "Frontend Engineer", "skill_name": "Web Performance Optimization", "demand_weight": 0.75},
    {"role_title": "Frontend Engineer", "skill_name": "Jest / React Testing Library", "demand_weight": 0.70},
    {"role_title": "Frontend Engineer", "skill_name": "Web Accessibility (WCAG / ARIA)", "demand_weight": 0.75},
    {"role_title": "Frontend Engineer", "skill_name": "Frontend Architecture", "demand_weight": 0.80},
    {"role_title": "Frontend Engineer", "skill_name": "Git / GitHub Workflows", "demand_weight": 0.85},

    # 1b. Senior React Developer
    {"role_title": "Senior React Developer", "skill_name": "React", "demand_weight": 0.98},
    {"role_title": "Senior React Developer", "skill_name": "TypeScript", "demand_weight": 0.95},
    {"role_title": "Senior React Developer", "skill_name": "JavaScript", "demand_weight": 0.92},
    {"role_title": "Senior React Developer", "skill_name": "Next.js", "demand_weight": 0.88},
    {"role_title": "Senior React Developer", "skill_name": "HTML5 / CSS3", "demand_weight": 0.85},
    {"role_title": "Senior React Developer", "skill_name": "Tailwind CSS", "demand_weight": 0.80},
    {"role_title": "Senior React Developer", "skill_name": "State Management (Redux/Zustand)", "demand_weight": 0.85},
    {"role_title": "Senior React Developer", "skill_name": "REST API Integration", "demand_weight": 0.85},
    {"role_title": "Senior React Developer", "skill_name": "Web Performance Optimization", "demand_weight": 0.82},
    {"role_title": "Senior React Developer", "skill_name": "Jest / React Testing Library", "demand_weight": 0.78},
    {"role_title": "Senior React Developer", "skill_name": "Web Accessibility (WCAG / ARIA)", "demand_weight": 0.75},
    {"role_title": "Senior React Developer", "skill_name": "Frontend Architecture", "demand_weight": 0.85},
    {"role_title": "Senior React Developer", "skill_name": "Git / GitHub Workflows", "demand_weight": 0.85},

    # 2. Backend Engineer
    {"role_title": "Backend Engineer", "skill_name": "Python", "demand_weight": 0.95},
    {"role_title": "Backend Engineer", "skill_name": "FastAPI", "demand_weight": 0.88},
    {"role_title": "Backend Engineer", "skill_name": "PostgreSQL", "demand_weight": 0.92},
    {"role_title": "Backend Engineer", "skill_name": "SQLAlchemy / ORM", "demand_weight": 0.85},
    {"role_title": "Backend Engineer", "skill_name": "RESTful API Architecture", "demand_weight": 0.90},
    {"role_title": "Backend Engineer", "skill_name": "Redis / Caching", "demand_weight": 0.82},
    {"role_title": "Backend Engineer", "skill_name": "Docker", "demand_weight": 0.85},
    {"role_title": "Backend Engineer", "skill_name": "Async Programming / asyncio", "demand_weight": 0.78},
    {"role_title": "Backend Engineer", "skill_name": "Microservices Architecture", "demand_weight": 0.75},
    {"role_title": "Backend Engineer", "skill_name": "Pytest / Unit Testing", "demand_weight": 0.80},

    # 3. Full-Stack Engineer
    {"role_title": "Full-Stack Engineer", "skill_name": "TypeScript", "demand_weight": 0.92},
    {"role_title": "Full-Stack Engineer", "skill_name": "React", "demand_weight": 0.90},
    {"role_title": "Full-Stack Engineer", "skill_name": "Node.js", "demand_weight": 0.85},
    {"role_title": "Full-Stack Engineer", "skill_name": "Python", "demand_weight": 0.88},
    {"role_title": "Full-Stack Engineer", "skill_name": "PostgreSQL", "demand_weight": 0.88},
    {"role_title": "Full-Stack Engineer", "skill_name": "Next.js", "demand_weight": 0.82},
    {"role_title": "Full-Stack Engineer", "skill_name": "Docker", "demand_weight": 0.80},
    {"role_title": "Full-Stack Engineer", "skill_name": "Git / GitHub Workflows", "demand_weight": 0.90},
    {"role_title": "Full-Stack Engineer", "skill_name": "GraphQL / REST APIs", "demand_weight": 0.78},
    {"role_title": "Full-Stack Engineer", "skill_name": "CI/CD Pipelines", "demand_weight": 0.75},

    # 4. Data Analyst
    {"role_title": "Data Analyst", "skill_name": "SQL", "demand_weight": 0.98},
    {"role_title": "Data Analyst", "skill_name": "Python", "demand_weight": 0.88},
    {"role_title": "Data Analyst", "skill_name": "Pandas / NumPy", "demand_weight": 0.85},
    {"role_title": "Data Analyst", "skill_name": "Tableau", "demand_weight": 0.82},
    {"role_title": "Data Analyst", "skill_name": "Power BI", "demand_weight": 0.80},
    {"role_title": "Data Analyst", "skill_name": "Excel (Advanced)", "demand_weight": 0.78},
    {"role_title": "Data Analyst", "skill_name": "Data Visualization", "demand_weight": 0.85},
    {"role_title": "Data Analyst", "skill_name": "Statistical Analysis", "demand_weight": 0.75},
    {"role_title": "Data Analyst", "skill_name": "Business Intelligence", "demand_weight": 0.82},

    # 5. Data Engineer
    {"role_title": "Data Engineer", "skill_name": "Python", "demand_weight": 0.95},
    {"role_title": "Data Engineer", "skill_name": "SQL", "demand_weight": 0.95},
    {"role_title": "Data Engineer", "skill_name": "Apache Spark", "demand_weight": 0.88},
    {"role_title": "Data Engineer", "skill_name": "Airflow", "demand_weight": 0.85},
    {"role_title": "Data Engineer", "skill_name": "Snowflake / BigQuery", "demand_weight": 0.88},
    {"role_title": "Data Engineer", "skill_name": "ETL Pipeline Design", "demand_weight": 0.92},
    {"role_title": "Data Engineer", "skill_name": "Kafka / Streaming Data", "demand_weight": 0.78},
    {"role_title": "Data Engineer", "skill_name": "Docker / Kubernetes", "demand_weight": 0.80},

    # 6. DevOps Engineer
    {"role_title": "DevOps Engineer", "skill_name": "Docker", "demand_weight": 0.95},
    {"role_title": "DevOps Engineer", "skill_name": "Kubernetes", "demand_weight": 0.92},
    {"role_title": "DevOps Engineer", "skill_name": "Terraform / IaC", "demand_weight": 0.90},
    {"role_title": "DevOps Engineer", "skill_name": "AWS / Cloud Infrastructure", "demand_weight": 0.92},
    {"role_title": "DevOps Engineer", "skill_name": "CI/CD (GitHub Actions / GitLab)", "demand_weight": 0.88},
    {"role_title": "DevOps Engineer", "skill_name": "Linux Systems Administration", "demand_weight": 0.85},
    {"role_title": "DevOps Engineer", "skill_name": "Bash / Python Scripting", "demand_weight": 0.85},
    {"role_title": "DevOps Engineer", "skill_name": "Prometheus / Grafana Monitoring", "demand_weight": 0.78},

    # 7. Machine Learning Engineer
    {"role_title": "Machine Learning Engineer", "skill_name": "Python", "demand_weight": 0.98},
    {"role_title": "Machine Learning Engineer", "skill_name": "PyTorch / TensorFlow", "demand_weight": 0.92},
    {"role_title": "Machine Learning Engineer", "skill_name": "Scikit-Learn", "demand_weight": 0.88},
    {"role_title": "Machine Learning Engineer", "skill_name": "MLOps / MLflow", "demand_weight": 0.85},
    {"role_title": "Machine Learning Engineer", "skill_name": "Feature Engineering", "demand_weight": 0.82},
    {"role_title": "Machine Learning Engineer", "skill_name": "Docker", "demand_weight": 0.80},
    {"role_title": "Machine Learning Engineer", "skill_name": "Model Deployment / FastAPI", "demand_weight": 0.85},
    {"role_title": "Machine Learning Engineer", "skill_name": "Linear Algebra & Statistics", "demand_weight": 0.78},

    # 8. AI / LLM Engineer
    {"role_title": "AI / LLM Engineer", "skill_name": "Python", "demand_weight": 0.98},
    {"role_title": "AI / LLM Engineer", "skill_name": "LangChain / LlamaIndex", "demand_weight": 0.90},
    {"role_title": "AI / LLM Engineer", "skill_name": "Vector Databases (pgvector/Pinecone)", "demand_weight": 0.88},
    {"role_title": "AI / LLM Engineer", "skill_name": "Prompt Engineering & RAG", "demand_weight": 0.92},
    {"role_title": "AI / LLM Engineer", "skill_name": "Groq / OpenAI API Integration", "demand_weight": 0.88},
    {"role_title": "AI / LLM Engineer", "skill_name": "PyTorch", "demand_weight": 0.80},
    {"role_title": "AI / LLM Engineer", "skill_name": "Model Fine-Tuning (LoRA)", "demand_weight": 0.78},
    {"role_title": "AI / LLM Engineer", "skill_name": "FastAPI", "demand_weight": 0.82},

    # 9. Product Manager
    {"role_title": "Product Manager", "skill_name": "Product Strategy & Vision", "demand_weight": 0.95},
    {"role_title": "Product Manager", "skill_name": "Agile / Scrum Methodology", "demand_weight": 0.90},
    {"role_title": "Product Manager", "skill_name": "User Research & Discovery", "demand_weight": 0.88},
    {"role_title": "Product Manager", "skill_name": "Roadmap Prioritization", "demand_weight": 0.92},
    {"role_title": "Product Manager", "skill_name": "Data Analytics (SQL/Amplitude)", "demand_weight": 0.80},
    {"role_title": "Product Manager", "skill_name": "Cross-Functional Leadership", "demand_weight": 0.90},
    {"role_title": "Product Manager", "skill_name": "JIRA / Productboard", "demand_weight": 0.78},
    {"role_title": "Product Manager", "skill_name": "A/B Testing & Experimentation", "demand_weight": 0.75},

    # 10. UX / UI Designer
    {"role_title": "UX / UI Designer", "skill_name": "Figma", "demand_weight": 0.98},
    {"role_title": "UX / UI Designer", "skill_name": "Wireframing & Prototyping", "demand_weight": 0.92},
    {"role_title": "UX / UI Designer", "skill_name": "User Journey Mapping", "demand_weight": 0.88},
    {"role_title": "UX / UI Designer", "skill_name": "Design Systems", "demand_weight": 0.90},
    {"role_title": "UX / UI Designer", "skill_name": "Usability Testing", "demand_weight": 0.85},
    {"role_title": "UX / UI Designer", "skill_name": "Information Architecture", "demand_weight": 0.82},
    {"role_title": "UX / UI Designer", "skill_name": "Visual Design & Typography", "demand_weight": 0.88},

    # 11. QA / Test Automation Engineer
    {"role_title": "QA / Test Automation Engineer", "skill_name": "Selenium / Playwright", "demand_weight": 0.92},
    {"role_title": "QA / Test Automation Engineer", "skill_name": "Python / JavaScript Scripting", "demand_weight": 0.88},
    {"role_title": "QA / Test Automation Engineer", "skill_name": "API Testing (Postman/Pytest)", "demand_weight": 0.90},
    {"role_title": "QA / Test Automation Engineer", "skill_name": "CI/CD Integration", "demand_weight": 0.80},
    {"role_title": "QA / Test Automation Engineer", "skill_name": "Test Strategy & Planning", "demand_weight": 0.85},
    {"role_title": "QA / Test Automation Engineer", "skill_name": "Jira / Bug Tracking", "demand_weight": 0.82},

    # 12. Cybersecurity Analyst
    {"role_title": "Cybersecurity Analyst", "skill_name": "SIEM Tools (Splunk/Elastic)", "demand_weight": 0.90},
    {"role_title": "Cybersecurity Analyst", "skill_name": "Network Security & Firewalls", "demand_weight": 0.88},
    {"role_title": "Cybersecurity Analyst", "skill_name": "Vulnerability Assessment", "demand_weight": 0.85},
    {"role_title": "Cybersecurity Analyst", "skill_name": "Incident Response", "demand_weight": 0.90},
    {"role_title": "Cybersecurity Analyst", "skill_name": "Identity & Access Management (IAM)", "demand_weight": 0.82},
    {"role_title": "Cybersecurity Analyst", "skill_name": "Compliance (SOC2 / ISO 27001)", "demand_weight": 0.78},

    # 13. Cloud Solutions Architect
    {"role_title": "Cloud Solutions Architect", "skill_name": "AWS Architecture", "demand_weight": 0.95},
    {"role_title": "Cloud Solutions Architect", "skill_name": "Azure / GCP", "demand_weight": 0.88},
    {"role_title": "Cloud Solutions Architect", "skill_name": "Terraform / IaC", "demand_weight": 0.90},
    {"role_title": "Cloud Solutions Architect", "skill_name": "Microservices & Serverless", "demand_weight": 0.85},
    {"role_title": "Cloud Solutions Architect", "skill_name": "Cloud Security & Governance", "demand_weight": 0.88},
    {"role_title": "Cloud Solutions Architect", "skill_name": "Disaster Recovery Planning", "demand_weight": 0.80},

    # 14. Site Reliability Engineer (SRE)
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "Kubernetes", "demand_weight": 0.95},
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "Prometheus & Grafana", "demand_weight": 0.90},
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "Go / Python", "demand_weight": 0.88},
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "SLO / SLA Management", "demand_weight": 0.85},
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "Chaos Engineering & Incident Management", "demand_weight": 0.80},
    {"role_title": "Site Reliability Engineer (SRE)", "skill_name": "Terraform", "demand_weight": 0.85},

    # 15. Systems Administrator
    {"role_title": "Systems Administrator", "skill_name": "Linux Administration (RHEL/Ubuntu)", "demand_weight": 0.95},
    {"role_title": "Systems Administrator", "skill_name": "Active Directory / LDAP", "demand_weight": 0.85},
    {"role_title": "Systems Administrator", "skill_name": "Bash / PowerShell Scripting", "demand_weight": 0.88},
    {"role_title": "Systems Administrator", "skill_name": "VMware / Hyper-V Virtualization", "demand_weight": 0.80},
    {"role_title": "Systems Administrator", "skill_name": "Network Troubleshooting", "demand_weight": 0.82},

    # 16. Database Administrator (DBA)
    {"role_title": "Database Administrator (DBA)", "skill_name": "PostgreSQL / MySQL Administration", "demand_weight": 0.95},
    {"role_title": "Database Administrator (DBA)", "skill_name": "Query Performance Tuning", "demand_weight": 0.92},
    {"role_title": "Database Administrator (DBA)", "skill_name": "Replication & Backup Recovery", "demand_weight": 0.88},
    {"role_title": "Database Administrator (DBA)", "skill_name": "SQL Expert", "demand_weight": 0.95},
    {"role_title": "Database Administrator (DBA)", "skill_name": "Database Security & Partitioning", "demand_weight": 0.82},

    # 17. Technical Program Manager (TPM)
    {"role_title": "Technical Program Manager (TPM)", "skill_name": "Cross-Team Program Execution", "demand_weight": 0.95},
    {"role_title": "Technical Program Manager (TPM)", "skill_name": "Software Architecture Fundamentals", "demand_weight": 0.88},
    {"role_title": "Technical Program Manager (TPM)", "skill_name": "Agile / Scrum Planning", "demand_weight": 0.90},
    {"role_title": "Technical Program Manager (TPM)", "skill_name": "Risk Mitigation & Stakeholder Management", "demand_weight": 0.92},
    {"role_title": "Technical Program Manager (TPM)", "skill_name": "JIRA / Confluence", "demand_weight": 0.85},

    # 18. Mobile App Developer (iOS/Android)
    {"role_title": "Mobile App Developer (iOS/Android)", "skill_name": "React Native / Flutter", "demand_weight": 0.90},
    {"role_title": "Mobile App Developer (iOS/Android)", "skill_name": "Swift / Kotlin", "demand_weight": 0.88},
    {"role_title": "Mobile App Developer (iOS/Android)", "skill_name": "Mobile UI/UX Conventions", "demand_weight": 0.82},
    {"role_title": "Mobile App Developer (iOS/Android)", "skill_name": "App Store & Play Store Publishing", "demand_weight": 0.78},
    {"role_title": "Mobile App Developer (iOS/Android)", "skill_name": "REST API Integration", "demand_weight": 0.85},

    # 19. Business Analyst
    {"role_title": "Business Analyst", "skill_name": "Requirements Gathering", "demand_weight": 0.95},
    {"role_title": "Business Analyst", "skill_name": "Process Mapping (BPMN)", "demand_weight": 0.88},
    {"role_title": "Business Analyst", "skill_name": "SQL & Data Analysis", "demand_weight": 0.85},
    {"role_title": "Business Analyst", "skill_name": "User Stories & Backlog Grooming", "demand_weight": 0.90},
    {"role_title": "Business Analyst", "skill_name": "Stakeholder Communication", "demand_weight": 0.92},

    # 20. Scrum Master / Agile Coach
    {"role_title": "Scrum Master / Agile Coach", "skill_name": "Scrum & Kanban Frameworks", "demand_weight": 0.98},
    {"role_title": "Scrum Master / Agile Coach", "skill_name": "Sprint Facilitation & Retrospectives", "demand_weight": 0.95},
    {"role_title": "Scrum Master / Agile Coach", "skill_name": "Jira / Targetprocess", "demand_weight": 0.85},
    {"role_title": "Scrum Master / Agile Coach", "skill_name": "Agile Coaching & Mentorship", "demand_weight": 0.88},
    {"role_title": "Scrum Master / Agile Coach", "skill_name": "Team Velocity Tracking", "demand_weight": 0.80},

    # 21. Data Scientist
    {"role_title": "Data Scientist", "skill_name": "Python", "demand_weight": 0.98},
    {"role_title": "Data Scientist", "skill_name": "R / Statistical Modeling", "demand_weight": 0.85},
    {"role_title": "Data Scientist", "skill_name": "SQL", "demand_weight": 0.92},
    {"role_title": "Data Scientist", "skill_name": "Machine Learning (Scikit-Learn)", "demand_weight": 0.90},
    {"role_title": "Data Scientist", "skill_name": "Data Visualization (Seaborn/Plotly)", "demand_weight": 0.82},

    # 22. Security Engineer
    {"role_title": "Security Engineer", "skill_name": "Application Security (OWASP Top 10)", "demand_weight": 0.95},
    {"role_title": "Security Engineer", "skill_name": "Penetration Testing", "demand_weight": 0.88},
    {"role_title": "Security Engineer", "skill_name": "Cryptography & PKI", "demand_weight": 0.80},
    {"role_title": "Security Engineer", "skill_name": "Python / Go Scripting", "demand_weight": 0.85},
    {"role_title": "Security Engineer", "skill_name": "Cloud Security Auditing", "demand_weight": 0.88},

    # 23. Network Engineer
    {"role_title": "Network Engineer", "skill_name": "Cisco CCNA / CCNP", "demand_weight": 0.92},
    {"role_title": "Network Engineer", "skill_name": "TCP/IP, BGP, OSPF Protocols", "demand_weight": 0.95},
    {"role_title": "Network Engineer", "skill_name": "Firewalls & VPN Configuration", "demand_weight": 0.88},
    {"role_title": "Network Engineer", "skill_name": "SD-WAN & Cloud Networking", "demand_weight": 0.80},
    {"role_title": "Network Engineer", "skill_name": "Wireshark Packet Analysis", "demand_weight": 0.82},

    # 24. Solutions Engineer
    {"role_title": "Solutions Engineer", "skill_name": "Pre-Sales Technical Presentations", "demand_weight": 0.92},
    {"role_title": "Solutions Engineer", "skill_name": "REST API & SDK Demos", "demand_weight": 0.88},
    {"role_title": "Solutions Engineer", "skill_name": "Proof of Concept (PoC) Build", "demand_weight": 0.90},
    {"role_title": "Solutions Engineer", "skill_name": "Technical Discovery & Scoping", "demand_weight": 0.85},
    {"role_title": "Solutions Engineer", "skill_name": "Solution Architecture Design", "demand_weight": 0.88},

    # 25. Embedded Systems Engineer
    {"role_title": "Embedded Systems Engineer", "skill_name": "C / C++", "demand_weight": 0.98},
    {"role_title": "Embedded Systems Engineer", "skill_name": "RTOS (Real-Time OS)", "demand_weight": 0.88},
    {"role_title": "Embedded Systems Engineer", "skill_name": "Microcontrollers (ARM / ESP32)", "demand_weight": 0.90},
    {"role_title": "Embedded Systems Engineer", "skill_name": "I2C, SPI, UART Protocols", "demand_weight": 0.85},
    {"role_title": "Embedded Systems Engineer", "skill_name": "Hardware Debugging (Oscilloscope)", "demand_weight": 0.78},

    # 26. Technical Support Engineer
    {"role_title": "Technical Support Engineer", "skill_name": "Root Cause Analysis", "demand_weight": 0.92},
    {"role_title": "Technical Support Engineer", "skill_name": "Zendesk / Ticket Management", "demand_weight": 0.88},
    {"role_title": "Technical Support Engineer", "skill_name": "SQL Debugging", "demand_weight": 0.82},
    {"role_title": "Technical Support Engineer", "skill_name": "Log Analysis & Diagnostics", "demand_weight": 0.85},
    {"role_title": "Technical Support Engineer", "skill_name": "Customer Escalation Handling", "demand_weight": 0.88},

    # 27. Game Developer
    {"role_title": "Game Developer", "skill_name": "Unity / Unreal Engine", "demand_weight": 0.95},
    {"role_title": "Game Developer", "skill_name": "C# / C++", "demand_weight": 0.95},
    {"role_title": "Game Developer", "skill_name": "3D Math & Physics Simulation", "demand_weight": 0.85},
    {"role_title": "Game Developer", "skill_name": "Shader Programming", "demand_weight": 0.78},
    {"role_title": "Game Developer", "skill_name": "Game State Management", "demand_weight": 0.82},

    # 28. Infrastructure Engineer
    {"role_title": "Infrastructure Engineer", "skill_name": "Terraform / Ansible", "demand_weight": 0.95},
    {"role_title": "Infrastructure Engineer", "skill_name": "Linux Administration", "demand_weight": 0.92},
    {"role_title": "Infrastructure Engineer", "skill_name": "AWS / GCP Networking", "demand_weight": 0.90},
    {"role_title": "Infrastructure Engineer", "skill_name": "Docker & Container Registries", "demand_weight": 0.88},
    {"role_title": "Infrastructure Engineer", "skill_name": "DNS & CDN Configuration", "demand_weight": 0.80},

    # 29. Technical Writer
    {"role_title": "Technical Writer", "skill_name": "API Documentation (OpenAPI/Swagger)", "demand_weight": 0.95},
    {"role_title": "Technical Writer", "skill_name": "Markdown & Docs-as-Code", "demand_weight": 0.90},
    {"role_title": "Technical Writer", "skill_name": "Developer Guides & Tutorials", "demand_weight": 0.88},
    {"role_title": "Technical Writer", "skill_name": "Git & Static Site Generators", "demand_weight": 0.82},
    {"role_title": "Technical Writer", "skill_name": "Information Architecture", "demand_weight": 0.80},

    # 30. Engineering Manager
    {"role_title": "Engineering Manager", "skill_name": "Engineering Team Leadership", "demand_weight": 0.98},
    {"role_title": "Engineering Manager", "skill_name": "Performance Management & 1:1s", "demand_weight": 0.95},
    {"role_title": "Engineering Manager", "skill_name": "Technical Hiring & Recruiting", "demand_weight": 0.90},
    {"role_title": "Engineering Manager", "skill_name": "Sprint Planning & Resource Allocation", "demand_weight": 0.88},
    {"role_title": "Engineering Manager", "skill_name": "Software Architecture Oversight", "demand_weight": 0.85},
]
