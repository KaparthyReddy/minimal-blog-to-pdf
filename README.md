# Minimal Blog-to-PDF Converter (blogprint)

A minimal, modular blog-to-PDF conversion tool that takes a blog URL, sanitizes and parses the content, and generates a clean, readable PDF.  
Implements a full content-processing pipeline including HTTP fetching (stubbed), DOM parsing, HTML cleanup, and structured PDF generation.

---

## 📋 Project Description

This project provides a lightweight service that:

- Accepts a blog/article URL  
- Fetches the article content (using mock fetch layer or actual requests)  
- Strips advertisements, boilerplate UI, and unnecessary elements  
- Parses and normalizes the HTML  
- Converts the cleaned content into a structured, readable PDF  

The system is designed with a **minimalist architecture** and **modular components** for parsing, transformation, and PDF rendering.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+  
- Required PDF-generation libraries (e.g., `reportlab`, `fpdf`)  
- `pip` package manager  

### Installation

```bash
git clone https://github.com/KaparthyReddy/blogprint.git
cd blogprint
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Run the application:

```bash
python backend/app.py
```

---

## 📁 Project Structure

```
backend/
    app.py
    requirements.txt

frontend/
    index.html
    script.js

integration_tests/
    integration_test.py
    integration_test2.py

metadata/
    metadata.py
    metadata_injector.py

system/
    system_part1.py
    system_part2.py

unit_tests/
    test_unit.py
    test_unit2.py

updated_backend/
    URL_validation.py
    pdf-style.css
    platform_cleanup.py
    remove_ads.py
    test_pdf_generation.py
```

---

## 🛠️ Development Guidelines

### Branching Strategy
- `main` — Stable, production-ready code  
- `dev` — Development & integration  
- `feature/*` — Feature-specific branches  
- `bugfix/*` — Bug fixes  

### Commit Messages (Conventional Format)
- `feat:` New features  
- `fix:` Bug fixes  
- `docs:` Documentation  
- `style:` Formatting / code style  
- `refactor:` Logic restructuring  
- `test:` Testing  

---

## ⚙️ CI/CD Pipeline

This project uses **GitHub Actions** for continuous integration and validation.

### Pipeline Stages

#### 1. Build (8–10s)
- Sets up Python 3.11  
- Installs dependencies from `backend/requirements.txt`  
- Verifies environment integrity  

#### 2. Test (18–22s)
- Runs all unit + integration tests  
- 27+ test cases  
- Validates core pipeline components  

#### 3. Coverage (12–15s)
- Coverage analysis with `pytest-cov`  
- HTML reports  
- **Current coverage: 84%**  

#### 4. Lint (10–13s)
- Static analysis with `pylint`  
- **Current score: 7.65/10**  

#### 5. Security (16–20s)
- Security scanning using `bandit`  
- Dependency checks using `safety`  

#### 6. Deploy (6–9s)
- Packages deployment artifact (.zip) including:  
  - Source code  
  - Test reports  
  - Documentation  

---

## 🚦 Quality Gates

The CI pipeline enforces:

- ✔️ 100% tests passing  
- ✔️ Code coverage ≥ 75%  
- ✔️ Pylint score ≥ 7.5/10  
- ✔️ No critical security vulnerabilities  

---

## ▶️ Running Locally

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend application
python app.py

# Run unit tests
pytest ../unit_tests/ -v

# Run integration tests
pytest ../integration_tests/ -v

# Check code coverage
pytest ../unit_tests/ --cov=. --cov-report=html --cov-report=term

# Check code quality
pylint app.py

# Security scan
bandit -r . -f json -o security-report.json
safety check
```

---

## 🧪 Testing

```bash
# Unit tests
pytest ../unit_tests/ -v

# Integration tests
pytest ../integration_tests/ -v

# Run tests with coverage report
pytest ../unit_tests/ --cov=. --cov-report=html --cov-report=term
```

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute for personal, research, or portfolio purposes.
