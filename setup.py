from setuptools import setup

setup(
    name="axiom-engine",
    version="1.0.0",
    description="Autonomous Self-Healing CI/CD Engine with Z3 Verification",
    author="Shyam",
    py_modules=[
        "axiom_cli",
        "engine",
        "llm",
        "memory",
        "chat",
        "github_ingestor",
        "axiom_enterprise",
    ],
    install_requires=[
        "python-dotenv",
        "requests",
        "groq",
        "qdrant-client",
        "z3-solver",
        "pytest",
    ],
)
