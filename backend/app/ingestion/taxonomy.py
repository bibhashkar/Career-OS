"""
Deterministic skills taxonomy and technical keyword aliases.

Maps acronyms, common variations, and frameworks to canonical names.
"""

from typing import Final

# Canonical skill name -> list of aliases/patterns (case-insensitive)
SKILL_TAXONOMY: Final[dict[str, list[str]]] = {
    # Languages
    "Python": ["python", "python3", "py"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "Java": ["java", "jvm"],
    "C++": ["c++", "cpp"],
    "SQL": ["sql"],
    # Backend Frameworks
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express": ["express", "express.js"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    # AI / LLM / Multi-Agent
    "LangGraph": ["langgraph"],
    "LangChain": ["langchain"],
    "LlamaIndex": ["llamaindex"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "tf"],
    "Hugging Face": ["hugging face", "huggingface"],
    "pgvector": ["pgvector", "pg-vector"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    # Data & Databases
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "Redis": ["redis"],
    "MongoDB": ["mongodb", "mongo"],
    "Elasticsearch": ["elasticsearch", "elastic"],
    "Cassandra": ["cassandra"],
    "Snowflake": ["snowflake"],
    "Kafka": ["kafka", "apache kafka"],
    # DevOps, Cloud & Infra
    "Docker": ["docker", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Azure": ["azure", "microsoft azure"],
    "Terraform": ["terraform", "tf"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "github actions"],
    # Frontend
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "GraphQL": ["graphql"],
    "REST": ["rest", "restful", "rest api"],
}
