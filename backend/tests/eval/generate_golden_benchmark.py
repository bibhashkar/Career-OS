"""
Deterministic Generator for the 25-Candidate x 500-Job Matching Golden Benchmark.

Generates:
1. 25 diverse candidate personas across all seniorities, verticals, and visa statuses.
2. 500 realistic, high-entropy job listings across 10 industry verticals and ATS providers.
3. Ground-truth graded relevance matrix (0=disqualified, 1=weak, 2=strong, 3=perfect).
4. Serializes output to backend/tests/eval/datasets/matching_golden_benchmark.json.
"""

import json
import random
from pathlib import Path
from typing import Any

RANDOM_SEED = 42

OUTPUT_PATH = Path(__file__).parent / "datasets" / "matching_golden_benchmark.json"

# ---------------------------------------------------------------------------
# Candidate Generation Specs
# ---------------------------------------------------------------------------
CANDIDATE_SPECS: list[dict[str, Any]] = [
    # 1-4: HealthTech Specialists
    {
        "id": "cand_ht_01",
        "name": "Elena Rostova",
        "headline": "Lead HealthTech & Clinical Systems Architect",
        "seniority": "staff",
        "years_experience": 12,
        "vertical": "healthtech",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 210000,
        "target_roles": ["Staff Backend Engineer", "Health Systems Architect"],
        "skills": [
            "Java",
            "Python",
            "AWS",
            "PostgreSQL",
            "Kafka",
            "EDI 837",
            "EDI 835",
            "FHIR",
            "HL7",
            "HIPAA",
        ],
        "blocks": [
            {
                "title": "Principal Health Systems Architect",
                "org": "Optum",
                "content": "Architected distributed HIPAA-compliant claims processing platform ingesting 15M daily EDI 837 and 835 transactions. Sub-50ms p99 latency.",
                "duration": 7,
                "metrics": {"qps": 5000, "throughput_or_latency": "p99 45ms"},
                "tags": ["healthtech"],
                "skills": [
                    "Java",
                    "Python",
                    "AWS",
                    "Kafka",
                    "EDI 837",
                    "EDI 835",
                    "HIPAA",
                ],
            },
            {
                "title": "Senior Clinical Data Engineer",
                "org": "Epic Systems",
                "content": "Engineered electronic health record (EHR) ingestion microservices converting HL7 v2 and DICOM feeds into PostgreSQL with PHI encryption.",
                "duration": 5,
                "metrics": {"throughput_or_latency": "100MB/s"},
                "tags": ["healthtech"],
                "skills": ["Java", "PostgreSQL", "HL7", "FHIR", "HIPAA", "EHR"],
            },
        ],
    },
    {
        "id": "cand_ht_02",
        "name": "Rajiv Patel",
        "headline": "Senior Healthcare Backend Platform Engineer",
        "seniority": "senior",
        "years_experience": 8,
        "vertical": "healthtech",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "New York, NY"],
        "min_salary": 175000,
        "target_roles": ["Senior Backend Engineer", "HealthTech Platform Engineer"],
        "skills": [
            "Python",
            "Java",
            "FastAPI",
            "PostgreSQL",
            "FHIR",
            "HL7",
            "HIPAA",
            "Docker",
            "AWS",
            "EDI 837",
            "EDI 835",
            "REST API",
        ],
        "blocks": [
            {
                "title": "Senior Backend Engineer",
                "org": "Oscar Health",
                "content": "Built FHIR and HL7 compliant patient telemetry APIs and prior authorization microservices in FastAPI and Java with PostgreSQL and REST API.",
                "duration": 5,
                "metrics": {"qps": 1200},
                "tags": ["healthtech"],
                "skills": [
                    "Python",
                    "Java",
                    "FastAPI",
                    "PostgreSQL",
                    "FHIR",
                    "HL7",
                    "HIPAA",
                    "REST API",
                ],
            },
            {
                "title": "Software Engineer",
                "org": "Cerner",
                "content": "Maintained clinical data integration workflows, EDI 835/837 claim feeds under HIPAA regulatory compliance.",
                "duration": 3,
                "metrics": {},
                "tags": ["healthtech"],
                "skills": ["Python", "AWS", "Docker", "HIPAA", "EDI 837", "EDI 835"],
            },
        ],
    },
    {
        "id": "cand_ht_03",
        "name": "Chloe Bennett",
        "headline": "Mid-Level Clinical Data Integrations Engineer",
        "seniority": "mid",
        "years_experience": 4,
        "vertical": "healthtech",
        "visa_status": "F-1 OPT",
        "remote_pref": "hybrid",
        "locations": ["Boston, MA"],
        "min_salary": 135000,
        "target_roles": ["Data Engineer", "HealthTech Backend Engineer"],
        "skills": [
            "Python",
            "PostgreSQL",
            "HL7",
            "FHIR",
            "Docker",
            "REST API",
            "HIPAA",
            "AWS",
            "EDI 837",
        ],
        "blocks": [
            {
                "title": "Clinical Integration Engineer",
                "org": "Flatiron Health",
                "content": "Developed HL7, FHIR, and EDI 837 ETL pipelines for real-world oncology clinical records on AWS.",
                "duration": 4,
                "metrics": {"data_volume": "10TB"},
                "tags": ["healthtech"],
                "skills": [
                    "Python",
                    "PostgreSQL",
                    "HL7",
                    "FHIR",
                    "HIPAA",
                    "AWS",
                    "EDI 837",
                ],
            }
        ],
    },
    {
        "id": "cand_ht_04",
        "name": "Liam Murphy",
        "headline": "Junior HealthTech Software Engineer",
        "seniority": "junior",
        "years_experience": 2,
        "vertical": "healthtech",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 105000,
        "target_roles": ["Junior Backend Engineer", "HealthTech Software Engineer"],
        "skills": [
            "Python",
            "SQL",
            "PostgreSQL",
            "REST API",
            "Git",
            "HIPAA",
            "FHIR",
            "HL7",
            "EDI 837",
        ],
        "blocks": [
            {
                "title": "Associate Software Engineer",
                "org": "Athenahealth",
                "content": "Assisted in maintaining billing integration APIs, FHIR/HL7 endpoints, and HIPAA-compliant audit logs.",
                "duration": 2,
                "metrics": {},
                "tags": ["healthtech"],
                "skills": [
                    "Python",
                    "PostgreSQL",
                    "Git",
                    "HIPAA",
                    "FHIR",
                    "HL7",
                    "EDI 837",
                ],
            }
        ],
    },
    # 5-8: FinTech & HFT / Quant Trading Specialists
    {
        "id": "cand_fin_01",
        "name": "Alexander Wei",
        "headline": "Staff Low-Latency Systems Architect & Quant Developer",
        "seniority": "staff",
        "years_experience": 13,
        "vertical": "hft_quant_trading",
        "visa_status": "Citizen",
        "remote_pref": "hybrid",
        "locations": ["New York, NY", "Chicago, IL"],
        "min_salary": 260000,
        "target_roles": [
            "Staff C++ Engineer",
            "Low Latency Architect",
            "Quant Developer",
        ],
        "skills": [
            "C++",
            "Low Latency C++",
            "Linux",
            "Concurrency",
            "Memory Management",
            "FIX Protocol",
            "Order Book",
            "Market Making",
            "FPGA",
        ],
        "blocks": [
            {
                "title": "Principal Core Systems Architect",
                "org": "Citadel",
                "content": "Engineered ultra-low latency direct market access execution gateways in modern C++ with sub-microsecond tick-to-trade latency.",
                "duration": 7,
                "metrics": {"throughput_or_latency": "sub-microsecond p99"},
                "tags": ["hft_quant_trading"],
                "skills": [
                    "C++",
                    "Low Latency C++",
                    "Linux",
                    "Concurrency",
                    "FIX Protocol",
                    "Order Book",
                ],
            },
            {
                "title": "Senior Quant Developer",
                "org": "Two Sigma",
                "content": "Built high-throughput equities matching engine simulators and order book processors.",
                "duration": 6,
                "metrics": {"qps": 250000},
                "tags": ["hft_quant_trading"],
                "skills": ["C++", "Linux", "Memory Management", "Market Making"],
            },
        ],
    },
    {
        "id": "cand_fin_02",
        "name": "Mei-Ling Zhou",
        "headline": "Senior FinTech Payments & Ledger Architect",
        "seniority": "senior",
        "years_experience": 9,
        "vertical": "fintech",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 185000,
        "target_roles": ["Senior Backend Engineer", "Staff Payments Engineer"],
        "skills": [
            "Go",
            "Java",
            "Python",
            "PostgreSQL",
            "Kafka",
            "Distributed Systems",
            "PCI-DSS",
            "ISO 20022",
            "Payments",
            "AWS",
            "Docker",
        ],
        "blocks": [
            {
                "title": "Senior Payments Infrastructure Engineer",
                "org": "Stripe",
                "content": "Designed double-entry general ledger microservices processing $4B annual transaction volume under PCI-DSS compliance using AWS and Docker.",
                "duration": 5,
                "metrics": {"volume": "$4B", "availability": "99.999%"},
                "tags": ["fintech"],
                "skills": [
                    "Go",
                    "Distributed Systems",
                    "Kafka",
                    "PostgreSQL",
                    "PCI-DSS",
                    "Payments",
                    "AWS",
                    "Docker",
                ],
            },
            {
                "title": "Software Engineer",
                "org": "Plaid",
                "content": "Built ACH and real-time bank account verification integrations.",
                "duration": 4,
                "metrics": {},
                "tags": ["fintech"],
                "skills": ["Go", "Java", "Python", "PostgreSQL", "ISO 20022"],
            },
        ],
    },
    {
        "id": "cand_fin_03",
        "name": "Lucas Rossi",
        "headline": "Senior Capital Markets Developer",
        "seniority": "senior",
        "years_experience": 7,
        "vertical": "hft_quant_trading",
        "visa_status": "Citizen",
        "remote_pref": "hybrid",
        "locations": ["Chicago, IL", "New York, NY"],
        "min_salary": 175000,
        "target_roles": ["C++ Developer", "Quant Systems Engineer"],
        "skills": [
            "C++",
            "Low Latency C++",
            "Linux",
            "Concurrency",
            "Memory Management",
            "FIX Protocol",
            "Order Book",
            "Python",
            "Multithreading",
            "SQL",
        ],
        "blocks": [
            {
                "title": "Trading Systems Engineer",
                "org": "Optiver",
                "content": "Maintained low-latency FIX protocol order routing hubs, memory management, and options order book pricing feeds in modern C++ and Linux.",
                "duration": 7,
                "metrics": {"throughput_or_latency": "p99 15us"},
                "tags": ["hft_quant_trading"],
                "skills": [
                    "C++",
                    "Low Latency C++",
                    "Linux",
                    "Concurrency",
                    "Memory Management",
                    "FIX Protocol",
                    "Order Book",
                    "Python",
                ],
            }
        ],
    },
    {
        "id": "cand_fin_04",
        "name": "Priya Sharma",
        "headline": "Mid-Level FinTech & Banking Platform Developer",
        "seniority": "mid",
        "years_experience": 4,
        "vertical": "fintech",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 140000,
        "target_roles": [
            "Backend Engineer",
            "FinTech Software Engineer",
            "Payments Engineer",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "AWS",
            "KYC/AML",
            "Payments",
            "PCI-DSS",
            "ISO 20022",
            "Kafka",
            "Docker",
            "REST API",
        ],
        "blocks": [
            {
                "title": "Backend Software Engineer",
                "org": "Brex",
                "content": "Built corporate credit card underwriting microservices, ISO 20022 payments integrations, and PCI-DSS compliant KYC verification pipelines using Kafka and AWS.",
                "duration": 4,
                "metrics": {"qps": 800},
                "tags": ["fintech"],
                "skills": [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "AWS",
                    "KYC/AML",
                    "Payments",
                    "PCI-DSS",
                    "ISO 20022",
                    "Kafka",
                ],
            }
        ],
    },
    # 9-12: AI / ML Infrastructure Specialists
    {
        "id": "cand_ai_01",
        "name": "David Kogan",
        "headline": "Principal AI/ML Infrastructure & GPU Systems Architect",
        "seniority": "principal",
        "years_experience": 15,
        "vertical": "ai_ml_infra",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 290000,
        "target_roles": ["Principal ML Infra Engineer", "Head of AI Infrastructure"],
        "skills": [
            "Python",
            "C++",
            "CUDA",
            "PyTorch",
            "Distributed Systems",
            "Ray",
            "Triton",
            "Kubernetes",
            "vLLM",
        ],
        "blocks": [
            {
                "title": "Staff AI Infrastructure Engineer",
                "org": "OpenAI",
                "content": "Architected multi-node distributed training clusters and high-throughput LLM model serving orchestration with custom CUDA kernels and Triton.",
                "duration": 8,
                "metrics": {"throughput_or_latency": "100k tokens/sec", "gpus": 4096},
                "tags": ["ai_ml_infra"],
                "skills": [
                    "CUDA",
                    "PyTorch",
                    "Distributed Systems",
                    "Ray",
                    "Kubernetes",
                    "Triton",
                ],
            },
            {
                "title": "Senior Systems Engineer",
                "org": "Databricks",
                "content": "Scaled Apache Spark and MLflow distributed model inference infrastructure.",
                "duration": 7,
                "metrics": {},
                "tags": ["ai_ml_infra"],
                "skills": ["Python", "C++", "Distributed Systems", "Kubernetes"],
            },
        ],
    },
    {
        "id": "cand_ai_02",
        "name": "Amina Touré",
        "headline": "Senior ML Platform & Serving Engineer",
        "seniority": "senior",
        "years_experience": 8,
        "vertical": "ai_ml_infra",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "Seattle, WA"],
        "min_salary": 180000,
        "target_roles": ["Senior ML Platform Engineer", "AI Infrastructure Engineer"],
        "skills": [
            "Python",
            "PyTorch",
            "CUDA",
            "Ray",
            "Triton",
            "vLLM",
            "Kubernetes",
            "Docker",
            "FastAPI",
            "AWS",
        ],
        "blocks": [
            {
                "title": "Senior ML Platform Engineer",
                "org": "Anthropic",
                "content": "Scaled LLM inference gateways, automated evaluation harnesses, and multi-agent workflow systems with vLLM, Ray, and FastAPI.",
                "duration": 5,
                "metrics": {"qps": 3500},
                "tags": ["ai_ml_infra"],
                "skills": ["Python", "PyTorch", "vLLM", "Ray", "Kubernetes", "FastAPI"],
            },
            {
                "title": "Machine Learning Engineer",
                "org": "Scale AI",
                "content": "Maintained annotation model validation pipelines in PyTorch and CUDA on AWS.",
                "duration": 3,
                "metrics": {},
                "tags": ["ai_ml_infra"],
                "skills": ["Python", "PyTorch", "CUDA", "Triton", "Docker", "AWS"],
            },
        ],
    },
    {
        "id": "cand_ai_03",
        "name": "Kenji Sato",
        "headline": "Mid-Level MLOps & Machine Learning Engineer",
        "seniority": "mid",
        "years_experience": 5,
        "vertical": "ai_ml_infra",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 150000,
        "target_roles": [
            "MLOps Engineer",
            "Machine Learning Engineer",
            "AI Infrastructure Engineer",
        ],
        "skills": [
            "Python",
            "C++",
            "PyTorch",
            "Ray",
            "Triton",
            "CUDA",
            "vLLM",
            "Distributed Systems",
            "Docker",
            "Kubernetes",
            "AWS",
            "PostgreSQL",
            "MLflow",
        ],
        "blocks": [
            {
                "title": "MLOps Engineer",
                "org": "Hugging Face",
                "content": "Maintained model registry, continuous integration evaluation pipelines, distributed systems training, and containerized Ray, vLLM, and Triton serving in C++ and Python on Kubernetes.",
                "duration": 5,
                "metrics": {},
                "tags": ["ai_ml_infra"],
                "skills": [
                    "Python",
                    "C++",
                    "PyTorch",
                    "Ray",
                    "Triton",
                    "CUDA",
                    "vLLM",
                    "Distributed Systems",
                    "Kubernetes",
                    "Docker",
                    "AWS",
                ],
            }
        ],
    },
    {
        "id": "cand_ai_04",
        "name": "Sofia Hernandez",
        "headline": "Junior AI & Deep Learning Software Engineer",
        "seniority": "junior",
        "years_experience": 2,
        "vertical": "ai_ml_infra",
        "visa_status": "F-1 OPT",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 115000,
        "target_roles": ["Junior ML Engineer", "AI Software Engineer"],
        "skills": ["Python", "PyTorch", "CUDA", "FastAPI", "Git", "Docker", "NumPy"],
        "blocks": [
            {
                "title": "AI Research Assistant",
                "org": "Stanford University",
                "content": "Trained vision-language models and fine-tuned transformers using PyTorch and CUDA on AWS GPU instances.",
                "duration": 2,
                "metrics": {},
                "tags": ["ai_ml_infra"],
                "skills": ["Python", "PyTorch", "CUDA", "FastAPI", "Docker", "Git"],
            }
        ],
    },
    # 13-16: DevTools & Cloud Infrastructure Specialists
    {
        "id": "cand_dev_01",
        "name": "Erik Lindqvist",
        "headline": "Staff Distributed Systems & Kubernetes Engineer",
        "seniority": "staff",
        "years_experience": 11,
        "vertical": "devtools",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 220000,
        "target_roles": ["Staff Systems Engineer", "Principal Infrastructure Engineer"],
        "skills": [
            "Go",
            "Kubernetes",
            "Docker",
            "Distributed Systems",
            "Terraform",
            "Linux",
            "gRPC",
            "Prometheus",
        ],
        "blocks": [
            {
                "title": "Staff Infrastructure Engineer",
                "org": "HashiCorp",
                "content": "Engineered core distributed consensus state engines in Go with Raft protocol, managing cluster orchestration across thousands of nodes.",
                "duration": 6,
                "metrics": {"nodes": 10000, "stars": 15000},
                "tags": ["devtools"],
                "skills": [
                    "Go",
                    "Distributed Systems",
                    "Kubernetes",
                    "Linux",
                    "Terraform",
                ],
            },
            {
                "title": "Senior Cloud Platform Engineer",
                "org": "Docker",
                "content": "Maintained container runtime interfaces and Linux cgroup isolation subsystems.",
                "duration": 5,
                "metrics": {},
                "tags": ["devtools"],
                "skills": ["Go", "Docker", "Linux", "Kubernetes"],
            },
        ],
    },
    {
        "id": "cand_dev_02",
        "name": "Tariq Mansour",
        "headline": "Senior Cloud Platform & SRE Engineer",
        "seniority": "senior",
        "years_experience": 8,
        "vertical": "devtools",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "Austin, TX"],
        "min_salary": 170000,
        "target_roles": [
            "Senior SRE",
            "Cloud Platform Engineer",
            "Senior Distributed Systems & Cloud Platform Engineer",
        ],
        "skills": [
            "Go",
            "Python",
            "Kubernetes",
            "AWS",
            "Terraform",
            "Prometheus",
            "CI/CD",
            "Docker",
            "Linux",
            "Distributed Systems",
            "gRPC",
        ],
        "blocks": [
            {
                "title": "Senior SRE",
                "org": "Datadog",
                "content": "Scaled telemetry ingestion and observability agents on Kubernetes across multi-cloud AWS and GCP deployments with Linux cgroup tuning and gRPC streaming.",
                "duration": 5,
                "metrics": {"qps": 80000},
                "tags": ["devtools"],
                "skills": [
                    "Go",
                    "Kubernetes",
                    "AWS",
                    "Prometheus",
                    "Terraform",
                    "Linux",
                    "gRPC",
                ],
            },
            {
                "title": "DevOps Engineer",
                "org": "GitLab",
                "content": "Built automated CI/CD runners, distributed systems workers, and deployment pipelines in Go, Linux, and Python.",
                "duration": 3,
                "metrics": {},
                "tags": ["devtools"],
                "skills": [
                    "Go",
                    "Python",
                    "CI/CD",
                    "Docker",
                    "Distributed Systems",
                    "Linux",
                ],
            },
        ],
    },
    {
        "id": "cand_dev_03",
        "name": "Olga Ivanova",
        "headline": "Senior Cybersecurity & Cloud Security Engineer",
        "seniority": "senior",
        "years_experience": 7,
        "vertical": "cybersecurity",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote", "Washington, DC"],
        "min_salary": 175000,
        "target_roles": ["Senior Security Engineer", "Cloud Security Architect"],
        "skills": [
            "Go",
            "Python",
            "FedRAMP",
            "SOC 2",
            "Kubernetes",
            "AWS",
            "Zero Trust",
            "SIEM",
        ],
        "blocks": [
            {
                "title": "Senior Security Engineer",
                "org": "CrowdStrike",
                "content": "Engineered endpoint telemetry ingestion and hardened cloud infrastructure to achieve FedRAMP High and SOC 2 Type II compliance.",
                "duration": 7,
                "metrics": {"compliance": "FedRAMP High"},
                "tags": ["cybersecurity"],
                "skills": ["Go", "Python", "FedRAMP", "SOC 2", "AWS", "Zero Trust"],
            }
        ],
    },
    {
        "id": "cand_dev_04",
        "name": "Jack Wilson",
        "headline": "Junior Cloud & DevOps Engineer",
        "seniority": "junior",
        "years_experience": 2,
        "vertical": "devtools",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 105000,
        "target_roles": ["Junior DevOps Engineer", "Cloud Engineer"],
        "skills": [
            "Python",
            "Go",
            "Docker",
            "Kubernetes",
            "Terraform",
            "Prometheus",
            "Linux",
            "Git",
            "AWS",
            "CI/CD",
        ],
        "blocks": [
            {
                "title": "Associate DevOps Engineer",
                "org": "Vercel",
                "content": "Maintained edge build worker infrastructure, Kubernetes clusters, and automated monitoring scripts with Terraform and Prometheus.",
                "duration": 2,
                "metrics": {},
                "tags": ["devtools"],
                "skills": [
                    "Python",
                    "Go",
                    "Docker",
                    "Kubernetes",
                    "Terraform",
                    "Linux",
                    "Git",
                ],
            }
        ],
    },
    # 17-20: Gaming & AdTech Specialists
    {
        "id": "cand_gam_01",
        "name": "Marcus Vance",
        "headline": "Senior Multiplayer Systems & Telemetry Architect",
        "seniority": "senior",
        "years_experience": 12,
        "vertical": "gaming",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote", "Los Angeles, CA"],
        "min_salary": 190000,
        "target_roles": ["Senior Backend Engineer", "Multiplayer Systems Engineer"],
        "skills": [
            "C++",
            "Java",
            "Python",
            "Unreal Engine",
            "Game Engine",
            "Gameplay",
            "Multiplayer Game",
            "Leaderboard",
            "AWS",
            "Kafka",
            "PostgreSQL",
        ],
        "blocks": [
            {
                "title": "Principal Game Backend Engineer",
                "org": "Riot Games",
                "content": "Architected low-latency multiplayer game matchmaking and leaderboards handling 600,000 concurrent players. Scaled distributed game server orchestration on AWS and Kafka event streaming with sub-20ms p99 latency.",
                "duration": 7,
                "metrics": {"throughput_or_latency": "p99 18ms", "ccu": 600000},
                "tags": ["gaming"],
                "skills": [
                    "C++",
                    "Java",
                    "Python",
                    "Unreal Engine",
                    "AWS",
                    "Kafka",
                    "Multiplayer Game",
                    "Leaderboard",
                ],
            },
            {
                "title": "Lead Telemetry & AdTech Engineer",
                "org": "The Trade Desk",
                "content": "Engineered real-time bidding DSP telemetry pipelines processing 200,000 queries per second into PostgreSQL data stores.",
                "duration": 5,
                "metrics": {"qps": 200000},
                "tags": ["adtech"],
                "skills": ["Java", "Python", "PostgreSQL", "Kafka"],
            },
        ],
    },
    {
        "id": "cand_gam_02",
        "name": "Felipe Santana",
        "headline": "Senior Game Engine & Gameplay Programmer",
        "seniority": "senior",
        "years_experience": 8,
        "vertical": "gaming",
        "visa_status": "Citizen",
        "remote_pref": "on_site",
        "locations": ["San Francisco, CA", "Seattle, WA"],
        "min_salary": 165000,
        "target_roles": ["Senior Gameplay Engineer", "Game Engine Developer"],
        "skills": [
            "C++",
            "Unreal Engine",
            "Game Engine",
            "Gameplay",
            "Shader",
            "Linux",
        ],
        "blocks": [
            {
                "title": "Senior Gameplay Engineer",
                "org": "Blizzard",
                "content": "Developed real-time character animation state machines and networking synchronization in Unreal Engine and modern C++.",
                "duration": 8,
                "metrics": {},
                "tags": ["gaming"],
                "skills": ["C++", "Unreal Engine", "Game Engine", "Gameplay"],
            }
        ],
    },
    {
        "id": "cand_gam_03",
        "name": "Zoe Kravitz",
        "headline": "Mid-Level Real-Time AdTech & Bidding Engineer",
        "seniority": "mid",
        "years_experience": 5,
        "vertical": "adtech",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "New York, NY"],
        "min_salary": 145000,
        "target_roles": ["AdTech Backend Engineer", "Distributed Systems Engineer"],
        "skills": ["Java", "Kafka", "Redis", "AWS", "Ad Tech", "RTB", "Microservices"],
        "blocks": [
            {
                "title": "Backend AdTech Engineer",
                "org": "AppLovin",
                "content": "Maintained high-throughput RTB bidding engines with sub-30ms SLA in Java and Redis.",
                "duration": 5,
                "metrics": {"throughput_or_latency": "sub-30ms SLA"},
                "tags": ["adtech"],
                "skills": ["Java", "Kafka", "Redis", "AWS", "Ad Tech", "RTB"],
            }
        ],
    },
    {
        "id": "cand_gam_04",
        "name": "Dante Rossi",
        "headline": "Junior Game Server Developer",
        "seniority": "junior",
        "years_experience": 2,
        "vertical": "gaming",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 95000,
        "target_roles": [
            "Junior Game Developer",
            "C++ Software Engineer",
            "Multiplayer Game Server Engineer",
        ],
        "skills": [
            "C++",
            "Python",
            "Unreal Engine",
            "Game Engine",
            "Gameplay",
            "Multiplayer Game",
            "AWS",
            "Kafka",
            "Linux",
            "Git",
        ],
        "blocks": [
            {
                "title": "Associate Game Programmer",
                "org": "Electronic Arts",
                "content": "Built telemetry logging tools, Unreal Engine multiplayer game mechanics, and automated matchmaking test suites in C++ and Python on AWS with Kafka.",
                "duration": 2,
                "metrics": {},
                "tags": ["gaming"],
                "skills": [
                    "C++",
                    "Python",
                    "Unreal Engine",
                    "Game Engine",
                    "Multiplayer Game",
                    "AWS",
                    "Kafka",
                    "Git",
                ],
            }
        ],
    },
    # 21-25: General Enterprise SaaS & Full-Stack Web Specialists
    {
        "id": "cand_saas_01",
        "name": "Hannah Abbott",
        "headline": "Staff Full-Stack & SaaS Platform Architect",
        "seniority": "staff",
        "years_experience": 11,
        "vertical": "general_saas",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 200000,
        "target_roles": ["Staff Software Engineer", "Full Stack Architect"],
        "skills": [
            "TypeScript",
            "Python",
            "React",
            "Next.js",
            "Node.js",
            "PostgreSQL",
            "GraphQL",
            "AWS",
            "Docker",
        ],
        "blocks": [
            {
                "title": "Staff Software Engineer",
                "org": "Atlassian",
                "content": "Architected multitenant Jira cloud workflow microservices supporting 250k enterprise tenants in TypeScript and React.",
                "duration": 6,
                "metrics": {"tenants": 250000},
                "tags": ["general_saas"],
                "skills": ["TypeScript", "React", "Node.js", "PostgreSQL", "AWS"],
            },
            {
                "title": "Senior Backend Engineer",
                "org": "Salesforce",
                "content": "Scaled customer data platform microservices in Python, PostgreSQL, and GraphQL.",
                "duration": 5,
                "metrics": {},
                "tags": ["general_saas"],
                "skills": ["Python", "PostgreSQL", "GraphQL", "Docker"],
            },
        ],
    },
    {
        "id": "cand_saas_02",
        "name": "Benjamin Clarke",
        "headline": "Senior Full-Stack & Python API Engineer",
        "seniority": "senior",
        "years_experience": 8,
        "vertical": "general_saas",
        "visa_status": "H-1B",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 165000,
        "target_roles": [
            "Senior Backend Engineer",
            "Full Stack Engineer",
            "Senior Full-Stack SaaS Platform Engineer",
        ],
        "skills": [
            "Python",
            "FastAPI",
            "Django",
            "PostgreSQL",
            "Redis",
            "Docker",
            "AWS",
            "TypeScript",
            "React",
            "Next.js",
            "Microservices",
        ],
        "blocks": [
            {
                "title": "Senior Backend Engineer",
                "org": "Dropbox",
                "content": "Engineered document preview synchronization APIs and React/Next.js dashboard components in FastAPI and PostgreSQL with Redis caching.",
                "duration": 5,
                "metrics": {"qps": 4000},
                "tags": ["general_saas"],
                "skills": [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Redis",
                    "AWS",
                    "React",
                    "TypeScript",
                ],
            },
            {
                "title": "Software Engineer",
                "org": "Zendesk",
                "content": "Maintained ticketing integrations and webhook ingestion microservices in Python, Next.js, and TypeScript.",
                "duration": 3,
                "metrics": {},
                "tags": ["general_saas"],
                "skills": ["Python", "Django", "PostgreSQL", "Docker", "Next.js"],
            },
        ],
    },
    {
        "id": "cand_saas_03",
        "name": "Maria Gonzalez",
        "headline": "Mid-Level React & TypeScript Frontend Specialist",
        "seniority": "mid",
        "years_experience": 5,
        "vertical": "general_saas",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 140000,
        "target_roles": ["Frontend Engineer", "Full Stack Engineer"],
        "skills": [
            "TypeScript",
            "React",
            "Next.js",
            "Tailwind CSS",
            "HTML",
            "CSS",
            "GraphQL",
        ],
        "blocks": [
            {
                "title": "Frontend Engineer",
                "org": "Shopify",
                "content": "Built high-performance merchant analytics dashboards in React, Next.js, and TypeScript with Tailwind CSS.",
                "duration": 5,
                "metrics": {"lighthouse_score": 98},
                "tags": ["general_saas"],
                "skills": ["TypeScript", "React", "Next.js", "Tailwind CSS", "GraphQL"],
            }
        ],
    },
    {
        "id": "cand_saas_04",
        "name": "Ethan Wright",
        "headline": "Junior Full Stack Developer",
        "seniority": "junior",
        "years_experience": 2,
        "vertical": "general_saas",
        "visa_status": "Citizen",
        "remote_pref": "remote",
        "locations": ["Remote"],
        "min_salary": 95000,
        "target_roles": ["Junior Full Stack Engineer", "Software Engineer"],
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "Git"],
        "blocks": [
            {
                "title": "Junior Full Stack Developer",
                "org": "HubSpot",
                "content": "Built CRM contact list filters and API integrations in Node.js and React.",
                "duration": 2,
                "metrics": {},
                "tags": ["general_saas"],
                "skills": ["TypeScript", "React", "Node.js", "PostgreSQL", "Git"],
            }
        ],
    },
    {
        "id": "cand_saas_05",
        "name": "Noah Kim",
        "headline": "Entry-Level Backend Software Engineer",
        "seniority": "entry",
        "years_experience": 1,
        "vertical": "general_saas",
        "visa_status": "F-1 OPT",
        "remote_pref": "remote",
        "locations": ["Remote", "San Francisco, CA"],
        "min_salary": 85000,
        "target_roles": [
            "Entry Level Backend Engineer",
            "Junior Developer",
            "Entry-Level Full-Stack SaaS Platform Engineer",
        ],
        "skills": [
            "Python",
            "TypeScript",
            "React",
            "Next.js",
            "AWS",
            "PostgreSQL",
            "FastAPI",
            "SQL",
            "Git",
            "Docker",
            "REST API",
        ],
        "blocks": [
            {
                "title": "Software Engineering Intern",
                "org": "Asana",
                "content": "Implemented automated unit tests, PostgreSQL queries, Next.js and React components, AWS cloud tasks, and internal FastAPI REST endpoints in Python and TypeScript.",
                "duration": 1,
                "metrics": {},
                "tags": ["general_saas"],
                "skills": [
                    "Python",
                    "TypeScript",
                    "React",
                    "Next.js",
                    "AWS",
                    "PostgreSQL",
                    "FastAPI",
                    "Git",
                    "REST API",
                ],
            }
        ],
    },
]

# ---------------------------------------------------------------------------
# Job Corpus Generation Archetypes
# ---------------------------------------------------------------------------
INDUSTRY_VERTICALS = [
    "healthtech",
    "fintech",
    "hft_quant_trading",
    "ai_ml_infra",
    "devtools",
    "cybersecurity",
    "gaming",
    "adtech",
    "general_saas",
    "ecommerce",
]

VERTICAL_COMPANIES: dict[str, list[str]] = {
    "healthtech": [
        "Optum",
        "Epic Systems",
        "Cerner",
        "Oscar Health",
        "Flatiron Health",
        "Athenahealth",
        "Veeva",
        "Teladoc",
    ],
    "fintech": [
        "Stripe",
        "Plaid",
        "Brex",
        "Ramp",
        "Robinhood",
        "Chime",
        "Affirm",
        "Block",
    ],
    "hft_quant_trading": [
        "Citadel",
        "Jane Street",
        "Two Sigma",
        "Hudson River Trading",
        "Optiver",
        "Jump Trading",
        "DRW",
        "Virtu",
    ],
    "ai_ml_infra": [
        "OpenAI",
        "Anthropic",
        "Scale AI",
        "Databricks",
        "Hugging Face",
        "Cohere",
        "Weights & Biases",
        "Mistral AI",
    ],
    "devtools": [
        "HashiCorp",
        "Docker",
        "Datadog",
        "GitLab",
        "GitHub",
        "Vercel",
        "Postman",
        "Supabase",
    ],
    "cybersecurity": [
        "CrowdStrike",
        "Palo Alto Networks",
        "Cloudflare",
        "Zscaler",
        "SentinelOne",
        "Okta",
        "Snyk",
        "Wiz",
    ],
    "gaming": [
        "Riot Games",
        "Blizzard",
        "Electronic Arts",
        "Epic Games",
        "Unity",
        "Roblox",
        "Ubisoft",
        "Respawn",
    ],
    "adtech": [
        "The Trade Desk",
        "AppLovin",
        "Criteo",
        "Magnite",
        "DoubleClick",
        "Integral Ad Science",
    ],
    "general_saas": [
        "Atlassian",
        "Salesforce",
        "Dropbox",
        "Zendesk",
        "Asana",
        "Slack",
        "Notion",
        "HubSpot",
    ],
    "ecommerce": [
        "Shopify",
        "Amazon",
        "Wayfair",
        "Instacart",
        "DoorDash",
        "Chewy",
        "Etsy",
        "eBay",
    ],
}

VERTICAL_TECH_POOLS: dict[str, list[str]] = {
    "healthtech": [
        "Python",
        "Java",
        "PostgreSQL",
        "AWS",
        "Kafka",
        "EDI 837",
        "EDI 835",
        "FHIR",
        "HL7",
        "HIPAA",
        "Docker",
        "REST API",
    ],
    "fintech": [
        "Go",
        "Java",
        "Python",
        "PostgreSQL",
        "Kafka",
        "Distributed Systems",
        "PCI-DSS",
        "ISO 20022",
        "Payments",
        "AWS",
        "Docker",
    ],
    "hft_quant_trading": [
        "C++",
        "Low Latency C++",
        "Linux",
        "Concurrency",
        "Memory Management",
        "FIX Protocol",
        "Order Book",
        "Market Making",
        "Python",
    ],
    "ai_ml_infra": [
        "Python",
        "C++",
        "CUDA",
        "PyTorch",
        "Distributed Systems",
        "Ray",
        "Triton",
        "Kubernetes",
        "Docker",
        "FastAPI",
        "AWS",
        "vLLM",
    ],
    "devtools": [
        "Go",
        "Kubernetes",
        "Docker",
        "Distributed Systems",
        "Terraform",
        "Linux",
        "gRPC",
        "Prometheus",
        "CI/CD",
        "AWS",
    ],
    "cybersecurity": [
        "Go",
        "Python",
        "FedRAMP",
        "SOC 2",
        "Kubernetes",
        "AWS",
        "Zero Trust",
        "SIEM",
        "Linux",
        "Docker",
    ],
    "gaming": [
        "C++",
        "Unreal Engine",
        "Java",
        "Python",
        "Game Engine",
        "Gameplay",
        "Leaderboard",
        "Multiplayer Game",
        "AWS",
        "Kafka",
    ],
    "adtech": [
        "Java",
        "Kafka",
        "Redis",
        "AWS",
        "Ad Tech",
        "RTB",
        "Microservices",
        "PostgreSQL",
        "Python",
    ],
    "general_saas": [
        "Python",
        "TypeScript",
        "React",
        "Next.js",
        "Node.js",
        "PostgreSQL",
        "GraphQL",
        "AWS",
        "FastAPI",
        "Docker",
    ],
    "ecommerce": [
        "Ruby",
        "Java",
        "TypeScript",
        "React",
        "PostgreSQL",
        "Redis",
        "Kafka",
        "AWS",
        "Docker",
        "GraphQL",
    ],
}

VERTICAL_SIGNATURE_PROTOCOLS: dict[str, list[str]] = {
    "healthtech": ["EDI 837", "EDI 835", "FHIR", "HL7", "HIPAA"],
    "fintech": ["PCI-DSS", "ISO 20022", "Payments"],
    "hft_quant_trading": [
        "FIX Protocol",
        "Order Book",
        "Market Making",
        "Low Latency C++",
    ],
    "ai_ml_infra": ["CUDA", "PyTorch", "Ray", "Triton", "vLLM"],
    "devtools": ["Kubernetes", "Terraform", "gRPC", "Prometheus"],
    "cybersecurity": ["FedRAMP", "SOC 2", "Zero Trust", "SIEM"],
    "gaming": ["Unreal Engine", "Game Engine", "Gameplay", "Multiplayer Game"],
    "adtech": ["Ad Tech", "RTB"],
    "general_saas": ["React", "PostgreSQL", "FastAPI"],
    "ecommerce": ["PostgreSQL", "Kafka", "Redis"],
}

LOCATIONS = [
    ("San Francisco, CA", "SF"),
    ("New York, NY", "NYC"),
    ("Seattle, WA", "SEA"),
    ("Austin, TX", "ATX"),
    ("Boston, MA", "BOS"),
    ("Chicago, IL", "CHI"),
    ("Remote", "REMOTE"),
]

SENIORITY_SALARY_RANGES = {
    "entry": (75000, 105000, 0),
    "junior": (95000, 130000, 2),
    "mid": (130000, 175000, 4),
    "senior": (165000, 220000, 7),
    "staff": (210000, 280000, 10),
    "principal": (260000, 360000, 14),
}


def generate_jobs_corpus(count: int = 500) -> list[dict[str, Any]]:
    """Generate 500 realistic, high-entropy job listings."""
    jobs: list[dict[str, Any]] = []

    for idx in range(1, count + 1):
        job_id = f"job_{idx:03d}"
        vertical = INDUSTRY_VERTICALS[idx % len(INDUSTRY_VERTICALS)]
        companies = VERTICAL_COMPANIES[vertical]
        company = companies[idx % len(companies)]

        # Seniority selection
        sen_keys = ["entry", "junior", "mid", "senior", "staff", "principal"]
        sen_weights = [0.08, 0.16, 0.32, 0.30, 0.10, 0.04]
        seniority = random.choices(sen_keys, weights=sen_weights, k=1)[0]
        min_base, max_base, min_years = SENIORITY_SALARY_RANGES[seniority]

        # Location & modality
        loc_tuple = random.choice(LOCATIONS)
        raw_location = loc_tuple[0]
        if raw_location == "Remote":
            workplace_type = "remote"
        else:
            workplace_type = random.choices(
                ["remote", "hybrid", "on_site"], weights=[0.45, 0.35, 0.20], k=1
            )[0]

        # Visa sponsorship policy
        visa_policy = random.choices(
            ["yes", "no", "transfer_only", "opt_cpt_accepted", None],
            weights=[0.40, 0.22, 0.10, 0.08, 0.20],
            k=1,
        )[0]

        # Domain strictness
        if vertical in ("healthtech", "hft_quant_trading", "cybersecurity"):
            strictness = random.choices([1.0, 0.5], weights=[0.70, 0.30], k=1)[0]
        elif vertical in ("fintech", "ai_ml_infra", "gaming", "devtools", "adtech"):
            strictness = random.choices(
                [1.0, 0.5, 0.0], weights=[0.35, 0.45, 0.20], k=1
            )[0]
        else:
            strictness = 0.0

        # Tech stack selection
        pool = list(VERTICAL_TECH_POOLS[vertical])
        sig_protocols = VERTICAL_SIGNATURE_PROTOCOLS.get(vertical, [])

        core_skills: list[str] = []
        if strictness == 1.0 and sig_protocols:
            mandate = random.choice(sig_protocols)
            core_skills.append(mandate)
        elif strictness == 0.5 and sig_protocols and random.random() < 0.7:
            mandate = random.choice(sig_protocols)
            core_skills.append(mandate)

        rem_pool = [s for s in pool if s not in core_skills]
        rem_count = random.randint(2, 4)
        core_skills.extend(random.sample(rem_pool, min(rem_count, len(rem_pool))))

        all_pool_rem = [s for s in pool if s not in core_skills]
        extra_count = random.randint(2, 3)
        extra_skills = random.sample(all_pool_rem, min(extra_count, len(all_pool_rem)))
        all_hard = list(dict.fromkeys(core_skills + extra_skills))

        # Title formatting
        sen_prefix = {
            "entry": "Entry-Level",
            "junior": "Junior",
            "mid": "Mid-Level",
            "senior": "Senior",
            "staff": "Staff",
            "principal": "Principal",
        }[seniority]
        role_label = {
            "healthtech": "Health Systems Platform Engineer",
            "fintech": "Payments & Financial Infrastructure Engineer",
            "hft_quant_trading": "Low-Latency Trading Systems Developer",
            "ai_ml_infra": "AI/ML Infrastructure & GPU Systems Engineer",
            "devtools": "Distributed Systems & Cloud Platform Engineer",
            "cybersecurity": "Cloud Security & Compliance Engineer",
            "gaming": "Multiplayer Game Server Engineer",
            "adtech": "Real-Time AdTech & Bidding Engineer",
            "general_saas": "Full-Stack SaaS Platform Engineer",
            "ecommerce": "E-Commerce Core Services Engineer",
        }[vertical]
        title = f"{sen_prefix} {role_label}"

        # Salary formatting (15% undisclosed)
        is_undisclosed = idx % 7 == 0
        salary_range = (
            None if is_undisclosed else f"${min_base // 1000}k - ${max_base // 1000}k"
        )

        # Age in days
        age_days = random.randint(0, 45)

        raw_desc = (
            f"{company} is hiring a {title} in {raw_location} ({workplace_type}). "
            f"Requirements: {', '.join(all_hard)}. Experience: {min_years}+ years. "
            f"{'Healthcare domain protocols and HIPAA experience required.' if strictness == 1.0 and vertical == 'healthtech' else ''}"
            f"{'FIX protocol and low-latency C++ experience required.' if strictness == 1.0 and vertical == 'hft_quant_trading' else ''}"
            f"{'FedRAMP/SOC 2 compliance background required.' if strictness == 1.0 and vertical == 'cybersecurity' else ''}"
        )

        job_dict = {
            "job_id": job_id,
            "title": title,
            "company_name": company,
            "industry": vertical,
            "industry_vertical": vertical,
            "domain_strictness": strictness,
            "raw_location": raw_location,
            "workplace_type": workplace_type,
            "salary_range": salary_range,
            "salary_min": None if is_undisclosed else min_base,
            "salary_max": None if is_undisclosed else max_base,
            "visa_sponsorship": visa_policy,
            "age_days": age_days,
            "raw_description": raw_desc,
            "ats_requirements": {
                "hard_skills": all_hard,
                "core_skills": core_skills,
                "years_experience_min": min_years,
                "seniority_level": seniority,
            },
        }
        jobs.append(job_dict)

    return jobs


def compute_ground_truth(
    candidate: dict[str, Any],
    job: dict[str, Any],
) -> int:
    """
    Determine objective ground truth relevance score (0, 1, 2, 3) for (candidate, job).

    3 (Perfect): Pass all gates, exact/compatible vertical match, seniority match or within 1 level,
                 strong core & hard skill overlap (>=60%), fresh posting (<=30 days), compensation feasible.
    2 (Strong): Pass all gates, vertical match or domain-agnostic, seniority within 1 level,
                solid skill overlap (>=40%), compensation feasible.
    1 (Weak): Pass legal gates, but significant gap in stack/seniority or stale/sub-par compensation.
    0 (Disqualified): Visa rejection, commuting mismatch, strict domain protocol missing,
                      or severe skill/seniority mismatch.
    """
    # 1. Hard Visa Gate
    cand_visa = candidate["visa_status"].strip().lower()
    cand_needs_visa = cand_visa in (
        "h-1b",
        "f-1 opt",
        "requires_sponsorship",
        "requires sponsorship",
    )
    job_visa = str(job.get("visa_sponsorship") or "").strip().lower()
    if cand_needs_visa and job_visa == "no":
        return 0

    # 2. Hard Location / Commuting Gate
    job_wp = str(job.get("workplace_type") or "remote").strip().lower()
    job_loc = str(job.get("raw_location") or "").strip().lower()
    is_remote_job = (job_wp == "remote") or ("remote" in job_loc)

    if not is_remote_job:
        cand_locs = [
            c.strip().lower()
            for c in candidate.get("locations", [])
            if c.strip().lower() != "remote"
        ]
        matched_loc = any(cloc in job_loc for cloc in cand_locs)
        if not matched_loc:
            return 0

    # 3. Domain Strictness Gate
    cand_vert = candidate["vertical"]
    job_vert = job["industry_vertical"]
    strictness = float(job.get("domain_strictness", 0.0))
    vertical_match = cand_vert == job_vert

    if strictness == 1.0 and not vertical_match:
        return 0

    # 4. Core Skills Overlap & Dealbreakers
    cand_skills_lower = {s.lower() for s in candidate["skills"]}
    job_core = [s.lower() for s in job["ats_requirements"].get("core_skills", [])]
    job_hard = [s.lower() for s in job["ats_requirements"].get("hard_skills", [])]

    core_overlap = sum(1 for s in job_core if s in cand_skills_lower) / max(
        1, len(job_core)
    )
    hard_overlap = sum(1 for s in job_hard if s in cand_skills_lower) / max(
        1, len(job_hard)
    )

    if core_overlap == 0.0 and len(job_core) > 0:
        return 0

    # 5. Seniority Alignment
    sen_ranks = {
        "entry": 0,
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "staff": 4,
        "principal": 5,
    }
    cand_rank = sen_ranks.get(candidate["seniority"], 2)
    job_rank = sen_ranks.get(job["ats_requirements"].get("seniority_level", "mid"), 2)
    sen_diff = abs(cand_rank - job_rank)

    if sen_diff >= 3:
        return 0

    cand_years = candidate.get("years_experience", 0)
    job_min_years = job["ats_requirements"].get("years_experience_min", 0)
    is_tenured_enough = job_min_years == 0 or cand_years >= job_min_years
    is_seniority_ideal = (cand_rank == job_rank) or (cand_rank == job_rank + 1)

    # 6. Compensation Feasibility
    cand_min = candidate.get("min_salary", 0)
    job_max = job.get("salary_max")
    severe_comp_mismatch = bool(job_max and cand_min > 0 and job_max < cand_min * 0.65)

    age_days = job.get("age_days", 10)
    is_fresh = age_days <= 45

    # 7. Graded Relevance Assignment
    # Relevance 3 (Perfect):
    if (
        vertical_match
        and is_seniority_ideal
        and is_tenured_enough
        and core_overlap >= 0.50
        and hard_overlap >= 0.45
        and is_fresh
        and not severe_comp_mismatch
    ):
        return 3

    # Relevance 2 (Strong):
    if not severe_comp_mismatch and (
        (
            vertical_match
            and sen_diff <= 1
            and (core_overlap >= 0.30 or hard_overlap >= 0.35)
        )
        or (vertical_match and sen_diff <= 2 and core_overlap >= 0.40)
        or (
            strictness == 0.0
            and sen_diff <= 1
            and (core_overlap >= 0.35 or hard_overlap >= 0.40)
        )
    ):
        return 2

    # Relevance 1 (Weak / Marginal / Stale / Below Salary):
    if sen_diff <= 2 and (core_overlap >= 0.20 or hard_overlap >= 0.20):
        return 1

    return 0
    return 0


def generate_benchmark_dataset() -> dict[str, Any]:
    """Assemble full benchmark dataset with ground-truth matrix."""
    random.seed(RANDOM_SEED)

    jobs = generate_jobs_corpus(count=500)
    candidates = CANDIDATE_SPECS

    # Compute ground-truth matrix
    ground_truth_matrix: dict[str, dict[str, int]] = {}
    for cand in candidates:
        cand_id = cand["id"]
        ground_truth_matrix[cand_id] = {}
        for job in jobs:
            rel = compute_ground_truth(cand, job)
            ground_truth_matrix[cand_id][job["job_id"]] = rel

    return {
        "metadata": {
            "name": "Career-OS Golden IR Matching Benchmark",
            "version": "2.0.0",
            "candidate_count": len(candidates),
            "job_count": len(jobs),
            "target_ndcg_at_10": 0.88,
            "target_mrr": 0.92,
            "target_precision_at_5": 0.80,
            "target_gate_leakage": 0.00,
            "target_p95_latency_ms": 45.0,
        },
        "candidates": candidates,
        "jobs": jobs,
        "ground_truth": ground_truth_matrix,
    }


def main() -> None:
    """Generate and write golden benchmark dataset to disk."""
    data = generate_benchmark_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated golden benchmark dataset at {OUTPUT_PATH}")
    print(f"Candidates: {len(data['candidates'])}, Jobs: {len(data['jobs'])}")


if __name__ == "__main__":
    main()
