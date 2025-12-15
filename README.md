**Enterprise Reverse Engineering Platform - User Guide & Setup**

**1\. Introduction**

This platform is an **Enterprise-Grade Reverse Engineering Tool** designed to analyze legacy codebases (Python, Java, C#, JS, etc.), extract business rules, and map dependencies using **Graph RAG** (Retrieval Augmented Generation).

It utilizes **Google Gemini 2.5 Pro** for reasoning, **PostgreSQL + pgvector** for memory/search, and **SQLAlchemy** for data management.

**2\. Prerequisites**

Before installing the application, ensure your machine meets the following requirements:

**A. Operating System**

- **Windows 10/11**, **Linux (Ubuntu 22.04+)**, or **macOS**.
- Minimum RAM: 8GB (16GB recommended for large codebases).

**B. Software Requirements**

You must have the following installed. Links are provided for download:

- **Git**: [Download for Windows/Mac/Linux](https://www.google.com/search?q=https://git-scm.com/downloads)
- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
  - _Note: On Windows, check the box "Add Python to PATH" during installation._
- **PostgreSQL 15+**: [Download PostgreSQL](https://www.postgresql.org/download/)
  - _Important:_ Remember the password you set for the postgres user during setup.

**3\. Database Setup (PostgreSQL + pgvector)**

This application requires the pgvector extension for semantic search.

**Step 1: Install PostgreSQL**

Run the installer downloaded in the previous step. Keep the default port (5432) and username (postgres).

**Step 2: Install pgvector**

- **Windows:**
  - Download the compiled installer from the [pgvector GitHub Releases](https://github.com/pgvector/pgvector/releases).
  - Run the installer. It will automatically detect your Postgres installation folder.
- **Linux/Mac:** Follow the [official installation instructions](https://github.com/pgvector/pgvector) (usually sudo apt install postgresql-15-pgvector).

**Step 3: Create Database**

Open your terminal (Command Prompt or PowerShell) and verify Postgres is running:

PowerShell

psql -U postgres

\# Enter your password when prompted

Inside the SQL prompt, run:

SQL

CREATE DATABASE reverse_engineering_kb;

\\c reverse_engineering_kb

CREATE EXTENSION vector;

\\q

**4\. Application Installation**

**Step 1: Clone the Repository**

Open a terminal in the folder where you want to keep the project:

PowerShell

git clone &lt;YOUR_GIT_REPO_URL&gt;

cd reverse-engineering-platform

**Step 2: Set Up Python Virtual Environment**

It is best practice to isolate dependencies.

PowerShell

\# Windows

python -m venv .venv

.venv\\Scripts\\activate

\# Mac/Linux

python3 -m venv .venv

source .venv/bin/activate

**Step 3: Install Dependencies**

Create or update your requirements.txt with the following critical packages:

**File:** requirements.txt

Plaintext

sqlalchemy>=2.0.0

alembic>=1.13.0

pgvector>=0.2.0

psycopg2>=2.9.0

google-generativeai>=0.8.0

pydantic-settings>=2.0.0

loguru>=0.7.0

gitpython>=3.1.0

pyyaml>=6.0.0

python-dotenv>=1.0.0

asyncio

Run the install command:

PowerShell

pip install -r requirements.txt

**5\. Configuration**

**Step 1: Environment Variables**

Create a file named .env in the root directory. Copy the content below and fill in your keys:

**File:** .env

Properties

\# LLM Provider Config

RE_LLM_PROVIDER=gemini

RE_MODEL_NAME=gemini-2.5-pro

\# Google AI Studio API Key (Required)

\# Get one here: <https://aistudio.google.com/app/apikey>

GOOGLE_API_KEY=your_actual_google_api_key_here

\# Database Config

RE_KB_DB_HOST=localhost

RE_KB_DB_PORT=5432

RE_KB_DB_NAME=reverse_engineering_kb

RE_KB_DB_USER=postgres

\# YOUR POSTGRES PASSWORD

RE_KB_DB_PASSWORD=your_postgres_password

DB_PASSWORD=your_postgres_password

**Step 2: Configure Codebases to Analyze**

Edit the config/codebases.yaml file to point to the local or remote git repositories you want to analyze.

**File:** config/codebases.yaml

YAML

codebases:

\- id: order-management-system

name: Order Management System

\# Can be a local path (C:/Projects/...) or a Git URL

source: <https://github.com/your-org/order-management.git>

language: python

priority: 1

**6\. Database Migration (Schema Setup)**

We use **Alembic** to create the tables automatically.

- **Initialize DB:**

PowerShell

alembic upgrade head

_Success Message:_ You should see output indicating it is running Initial schema... and finishing without errors.

_Troubleshooting:_ If you see authentication errors, ensure DB_PASSWORD in your .env file matches your local Postgres password.

**7\. Running the Tool**

To start the analysis pipeline (Discovery -> Indexing -> Analysis):

PowerShell

python run.py

**What to Expect:**

- **Phase 1 (Discovery):** The tool checks config/codebases.yaml, clones any git repos, and registers the project in the DB.
- **Phase 2 (Indexing):** It scans all files to build the **Dependency Graph** (finding imports and definitions).
- **Phase 3 (Analysis):** It sends each file to Gemini (LLM) along with the context of its dependencies to extract business rules.
- **Phase 4 (Reporting):** Generates a comprehensive project summary report in Markdown, including Business Rules, Code Summaries, and Dependency Graphs.
- **Completion:** Check the logs/ folder for detailed outputs.

**8\. Report Generation**

The platform generates human-readable Markdown reports for each analysis run.

**Automatic Reporting**
Reports are automatically generated at the end of Phase 4 and saved to the `reports/` directory.
- **Format:** `reports/{Project_Name}_{Run_ID}_{Timestamp}_Summary.md`

**Standalone Report Generator**
You can regenerate a report for a specific past analysis run without re-running the entire analysis (saving time and tokens).

**Usage:**
```powershell
python generate_report_only.py --run-id <YOUR_RUN_UUID>
```
*Note: You can find the Run ID in the existing report filenames or by querying the `analysis_runs` table.*

**Rate Limit Handling (Smart Throttling)**
The system includes built-in intelligence to handle LLM rate limits (429 Errors):
- **Predictive Throttling:** Estimates token usage before generating reports and automatically pauses to refill the quota if the payload is too large.
- **Smart Retries:** Parses "Retry-After" headers from the API to wait exactly as long as needed.

**9\. Viewing Results**

**Option A: Generated Reports**
Open the `reports/` directory to view the detailed Markdown summaries.

**Option B: Database Queries**
Results are stored in PostgreSQL. You can query them using a tool like **pgAdmin** or **DBeaver**.

**Useful SQL Queries:**

- **Check Analysis Run Status:**
```sql
SELECT run_id, project_id, status, created_at FROM analysis_runs ORDER BY created_at DESC;
```

- **See all Extracted Rules:**
```sql
SELECT title, description, code_snippet FROM business_rules;
```

- **See Rules for a Specific File:**
```sql
SELECT * FROM business_rules WHERE file_path LIKE '%order_strategy.py%';
```

- **Check Dependency Graph:**
```sql
SELECT * FROM file_dependencies LIMIT 20;
```