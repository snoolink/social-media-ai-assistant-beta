#!/usr/bin/env python3
"""
Resume Customizer CLI
Usage:
    python customize_resume.py --template <path_to_template.docx> --url <job_url>
    python customize_resume.py --url <job_url>   # uses default template
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import boto3
import requests
from bs4 import BeautifulSoup

# ── Config ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("customized_resumes")
TEMPLATE_JS = Path(__file__).parent / "template.js"

# Bedrock configuration
AWS_REGION = "us-east-1"
BEDROCK_MODEL_ID = "google.gemma-3-12b-it"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_bedrock_client():
    """Return a boto3 Bedrock Runtime client."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def invoke_bedrock(client, prompt: str, max_tokens: int = 4000) -> str:
    """
    Call the Bedrock Converse API with the configured model.
    Returns the text response as a string.
    """
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": max_tokens,
        },
    )
    return response["output"]["message"]["content"][0]["text"]


# ── Scraper ────────────────────────────────────────────────────────────────────

def scrape_job(url: str) -> str:
    """Fetch job page and return cleaned text. Falls back to Bedrock on failure."""
    print(f"  Fetching: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe", "aside", "form"]):
            tag.decompose()

        selectors = [
            {"attrs": {"data-automation": "jobDescription"}},
            {"class_": re.compile(r"job.?desc|posting|description|content|detail", re.I)},
            {"id": re.compile(r"job.?desc|posting|description|content|detail", re.I)},
        ]
        body = None
        for sel in selectors:
            found = soup.find(True, **sel)
            if found and len(found.get_text(strip=True)) > 200:
                body = found
                break

        text = (body or soup.find("body") or soup).get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        cleaned = "\n".join(lines)
        print(f"  Scraped {len(cleaned):,} characters of text.")
        return cleaned

    except Exception as e:
        print(f"  Warning: direct fetch failed ({e}). Trying fallback...")
        return scrape_via_fallback(url)


def scrape_via_fallback(url: str) -> str:
    """Use Bedrock as a fallback."""
    client = get_bedrock_client()
    prompt = (
        f"Please retrieve and summarize the full job description from this URL: {url}\n"
        "Include job title, company, location, responsibilities, and all qualifications."
    )
    text = invoke_bedrock(client, prompt, max_tokens=4000)
    print(f"  Fallback retrieved {len(text):,} characters.")
    return text


# ── Bedrock: Extract job intelligence ─────────────────────────────────────────

def extract_job_info(raw_text: str, url: str) -> dict:
    """Send scraped text to Bedrock and get structured job intelligence back as JSON."""
    print("  Analyzing job description with Bedrock...")
    client = get_bedrock_client()

    prompt = f"""
You are a resume strategist. Analyze this job description scraped from {url} and return ONLY valid JSON — no markdown, no explanation.

JOB DESCRIPTION:
{raw_text[:12000]}

Return this exact JSON structure:
{{
  "job_title": "...",
  "company": "...",
  "location": "...",
  "summary": "...",
  "key_responsibilities": ["...", "...", "..."],
  "required_skills": ["...", "..."],
  "preferred_skills": ["...", "..."],
  "keywords": ["...", "..."],
  "tone": "...",
  "adapted_experiences": {{
    "growmark": ["Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4", "Bullet 5", "Bullet 6"],
    "normal": ["Bullet 1", "Bullet 2", "Bullet 3"],
    "cadence": ["Bullet 1", "Bullet 2", "Bullet 3"]
  }},
  "adapted_summary": "...",
  "adapted_snoolink_bullets": ["Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4"]
}}

Rules for rewriting bullets:
- Keep all facts true (same companies, same projects, same technologies actually used)
- Mirror the JD's vocabulary and terminology
- Emphasize whichever skills and outcomes are most relevant to THIS role
- No dashes (em dash, en dash, or hyphen used as connector) anywhere in the output
- No markdown formatting in bullet text
- Each bullet should be 1-2 sentences, action-verb first
"""

    raw_json = invoke_bedrock(client, prompt, max_tokens=4000).strip()
    raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json)
    raw_json = re.sub(r"\n?```$", "", raw_json)

    try:
        data = json.loads(raw_json)
        print(f"  Job: {data.get('job_title')} at {data.get('company')} ({data.get('location')})")
        return data
    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse failed ({e}). Using defaults.")
        return {
            "job_title": "Data Engineer",
            "company": "Unknown",
            "location": "Chicago, IL",
            "adapted_summary": "",
            "adapted_experiences": {"growmark": [], "normal": [], "cadence": []},
            "adapted_snoolink_bullets": [],
            "keywords": [],
            "required_skills": [],
            "preferred_skills": [],
        }


# ── JS Resume Builder ──────────────────────────────────────────────────────────

def build_resume_js(job: dict, output_docx: Path) -> str:
    """Generate the Node.js resume script with all content replaced."""

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()

    def bullets_js(items: list, fallback_lines: list) -> str:
        """Return JS bullet() calls from items, or fallback_lines if items is empty."""
        source = items if items else fallback_lines
        return "\n      ".join(f'bullet("{esc(b)}"),' for b in source)

    location  = esc(job.get("location", "Chicago, IL"))
    summary   = esc(job.get("adapted_summary", ""))
    exp       = job.get("adapted_experiences", {})

    # Pre-compute all bullet blocks BEFORE the f-string to avoid
    # SyntaxError: f-string cannot contain triple-quoted strings
    g_bullets = bullets_js(exp.get("growmark", []), [
        "Design, build, and maintain large-scale data pipelines and ETL workflows supporting mission-critical analytics and business decision-making across agriculture supply chain operations.",
        "Own data lifecycle management for core datasets, defining data models, managing SLAs for pipeline freshness and uptime, and triaging data incidents to resolution with minimal business impact.",
        "Develop complex SQL queries and Python-based data transformation jobs processing high-volume structured datasets; optimize through indexing, query refactoring, and pipeline parallelization.",
        "Collaborate cross-functionally with data scientists, analysts, and product stakeholders to prototype metrics, validate schema designs, and translate requirements into robust data solutions.",
        "Implement data quality frameworks and automated anomaly detection to intercept issues before reaching downstream consumers, establishing standard methodologies for pipeline reliability.",
        "Contribute to analytics infrastructure tooling and frameworks that improve efficiency of data platform management and deployment across the team.",
    ])

    n_bullets = bullets_js(exp.get("normal", []), [
        "Developed and maintained data pipelines and reporting systems for municipal operations, transforming raw government datasets into clean, queryable analytics-ready datasets.",
        "Built and documented data models and lifecycle workflows to support operational reporting and data-driven decision-making across city departments.",
        "Delivered data quality improvements by identifying schema inconsistencies and implementing validation logic, reducing reporting errors for key civic metrics.",
    ])

    c_bullets = bullets_js(exp.get("cadence", []), [
        "Engineered backend systems and data processing pipelines for EDA software used by large-scale semiconductor clients, working with high-volume structured data.",
        "Developed scalable Java services and Python scripts to process complex design datasets, improving throughput and reliability of data-intensive workflows in production.",
        "Collaborated with cross-functional engineering teams on distributed systems design, debugging pipeline failures, and optimizing data processing performance.",
    ])

    sn_bullets = bullets_js(job.get("adapted_snoolink_bullets", []), [
        "Architected and built an end-to-end AI data pipeline using computer vision (OpenAI CLIP, BLIP) and NLP to ingest, analyze, and semantically index 10,000+ images and videos, enabling natural language querying over unstructured media at scale.",
        "Engineered a scalable data serving layer using FastAPI, PostgreSQL, and FAISS vector database, owning the full pipeline from ingestion to query layer and achieving 95% accuracy in semantic image retrieval.",
        "Debugged and resolved a critical vector index inconsistency causing silent retrieval failures, traced root cause to async write conflicts and implemented locking logic to guarantee data consistency.",
        "Independently designed the data ontology and schema for a multi-modal AI asset store, establishing lifecycle management policies and data quality standards for all stored entities.",
    ])

    output_docx_str = str(output_docx)

    script = f'''const {{
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType,
  TabStopType
}} = require('docx');
const fs = require('fs');

const NAVY = "1B2A4A";
const ACCENT = "2E75B6";
const MID_GRAY = "D0D7E3";
const TEXT_DARK = "1A1A2E";
const TEXT_MED = "4A4A6A";

const PAGE_WIDTH = 12240;
const MARGIN = 900;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

function sectionHeader(title) {{
  return new Paragraph({{
    spacing: {{ before: 240, after: 80 }},
    border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 4 }} }},
    children: [new TextRun({{ text: title.toUpperCase(), bold: true, size: 22, color: NAVY, font: "Calibri", characterSpacing: 40 }})]
  }});
}}

function jobTitle(title, company, location, dates) {{
  return [
    new Paragraph({{
      spacing: {{ before: 160, after: 40 }},
      tabStops: [{{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }}],
      children: [
        new TextRun({{ text: title, bold: true, size: 22, color: TEXT_DARK, font: "Calibri" }}),
        new TextRun({{ text: "\\t", font: "Calibri" }}),
        new TextRun({{ text: dates, size: 20, color: TEXT_MED, italics: true, font: "Calibri" }}),
      ]
    }}),
    new Paragraph({{
      spacing: {{ before: 0, after: 60 }},
      children: [
        new TextRun({{ text: company, bold: true, size: 20, color: ACCENT, font: "Calibri" }}),
        new TextRun({{ text: "  |  " + location, size: 20, color: TEXT_MED, font: "Calibri" }}),
      ]
    }})
  ];
}}

function bullet(text) {{
  return new Paragraph({{
    numbering: {{ reference: "bullets", level: 0 }},
    spacing: {{ before: 30, after: 30 }},
    children: [new TextRun({{ text, size: 20, color: TEXT_DARK, font: "Calibri" }})]
  }});
}}

function skillRow(category, skills) {{
  const catWidth = 2300;
  const skillWidth = CONTENT_WIDTH - catWidth;
  const nb = {{ style: BorderStyle.NONE, size: 0, color: "FFFFFF" }};
  const borders = {{ top: nb, bottom: nb, left: nb, right: nb }};
  return new TableRow({{
    children: [
      new TableCell({{
        borders, width: {{ size: catWidth, type: WidthType.DXA }},
        margins: {{ top: 55, bottom: 55, left: 60, right: 120 }},
        children: [new Paragraph({{ children: [new TextRun({{ text: category, bold: true, size: 20, color: NAVY, font: "Calibri" }})] }})]
      }}),
      new TableCell({{
        borders, width: {{ size: skillWidth, type: WidthType.DXA }},
        margins: {{ top: 55, bottom: 55, left: 60, right: 60 }},
        children: [new Paragraph({{ children: [new TextRun({{ text: skills, size: 20, color: TEXT_DARK, font: "Calibri" }})] }})]
      }}),
    ]
  }});
}}

const doc = new Document({{
  numbering: {{
    config: [{{
      reference: "bullets",
      levels: [{{
        level: 0, format: LevelFormat.BULLET, text: "▸", alignment: AlignmentType.LEFT,
        style: {{ paragraph: {{ indent: {{ left: 420, hanging: 260 }} }} }}
      }}]
    }}]
  }},
  styles: {{ default: {{ document: {{ run: {{ font: "Calibri", size: 20, color: TEXT_DARK }} }} }} }},
  sections: [{{
    properties: {{
      page: {{
        size: {{ width: PAGE_WIDTH, height: 15840 }},
        margin: {{ top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }}
      }}
    }},
    children: [

      // HEADER
      new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ before: 0, after: 60 }},
        children: [new TextRun({{ text: "JAY DEV", bold: true, size: 56, color: NAVY, font: "Calibri" }})]
      }}),
      new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ before: 0, after: 80 }},
        children: [new TextRun({{ text: "Senior Data Engineer", size: 28, color: ACCENT, font: "Calibri", bold: true }})]
      }}),
      new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ before: 0, after: 20 }},
        border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 8 }} }},
        children: [
          new TextRun({{ text: "jaytalksdata@gmail.com", size: 19, color: TEXT_MED, font: "Calibri" }}),
          new TextRun({{ text: "  ·  ", size: 19, color: MID_GRAY, font: "Calibri" }}),
          new TextRun({{ text: "(309) 612-4869", size: 19, color: TEXT_MED, font: "Calibri" }}),
          new TextRun({{ text: "  ·  ", size: 19, color: MID_GRAY, font: "Calibri" }}),
          new TextRun({{ text: "linkedin.com/in/neuronjay", size: 19, color: TEXT_MED, font: "Calibri" }}),
          new TextRun({{ text: "  ·  ", size: 19, color: MID_GRAY, font: "Calibri" }}),
          new TextRun({{ text: "github.com/neuronjay", size: 19, color: TEXT_MED, font: "Calibri" }}),
          new TextRun({{ text: "  ·  ", size: 19, color: MID_GRAY, font: "Calibri" }}),
          new TextRun({{ text: "{location}", size: 19, color: TEXT_MED, font: "Calibri" }}),
        ]
      }}),
      new Paragraph({{ spacing: {{ before: 100, after: 0 }}, children: [] }}),

      // PROFESSIONAL SUMMARY
      sectionHeader("Professional Summary"),
      new Paragraph({{
        spacing: {{ before: 80, after: 80 }},
        children: [new TextRun({{ text: "{summary}", size: 20, color: TEXT_DARK, font: "Calibri" }})]
      }}),

      // PROFESSIONAL EXPERIENCE
      sectionHeader("Professional Experience"),

      ...jobTitle("Data Engineer", "Growmark, Inc.", "Bloomington, IL", "2022 to Present"),
      {g_bullets}

      ...jobTitle("Data Specialist", "Town of Normal City Department", "Normal, IL", "2022"),
      {n_bullets}

      ...jobTitle("Software Engineer", "Cadence Design Systems", "San Jose, CA", "2020 to 2021"),
      {c_bullets}

      // KEY PROJECTS
      sectionHeader("Key Projects"),

      new Paragraph({{
        spacing: {{ before: 140, after: 40 }},
        tabStops: [{{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }}],
        children: [
          new TextRun({{ text: "Snoolink  AI-Powered Content Management Platform", bold: true, size: 21, color: TEXT_DARK, font: "Calibri" }}),
          new TextRun({{ text: "\\t", font: "Calibri" }}),
          new TextRun({{ text: "snoolink.com  |  Present", size: 19, color: TEXT_MED, italics: true, font: "Calibri" }}),
        ]
      }}),
      {sn_bullets}

      new Paragraph({{
        spacing: {{ before: 140, after: 40 }},
        children: [
          new TextRun({{ text: "DNA Test Data Privacy  Published Research  |  Springer Link", bold: true, size: 21, color: TEXT_DARK, font: "Calibri" }}),
        ]
      }}),
      bullet("Conducted and published research on privacy risks in DNA test datasets, contributing to advancements in ethical data handling and data security methodologies relevant to large-scale consumer data stewardship."),

      // EDUCATION
      sectionHeader("Education"),

      new Paragraph({{
        spacing: {{ before: 100, after: 40 }},
        tabStops: [{{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }}],
        children: [
          new TextRun({{ text: "M.S. Computer Science  Data Systems Track", bold: true, size: 22, color: TEXT_DARK, font: "Calibri" }}),
          new TextRun({{ text: "\\t", font: "Calibri" }}),
          new TextRun({{ text: "2021", size: 20, color: TEXT_MED, italics: true, font: "Calibri" }}),
        ]
      }}),
      new Paragraph({{
        spacing: {{ before: 0, after: 40 }},
        children: [new TextRun({{ text: "Illinois State University, IL", size: 20, color: ACCENT, font: "Calibri", bold: true }})]
      }}),
      bullet("Graduate Teaching Assistant  IT 168: Structured Problem-Solving using Java"),
      bullet("Published research on DNA test data privacy, contributing to advancements in data security and ethical data handling (Springer Link)"),

      new Paragraph({{
        spacing: {{ before: 100, after: 40 }},
        tabStops: [{{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }}],
        children: [
          new TextRun({{ text: "B.S. Information Technology  Honors in Computational Science", bold: true, size: 22, color: TEXT_DARK, font: "Calibri" }}),
          new TextRun({{ text: "\\t", font: "Calibri" }}),
          new TextRun({{ text: "2017", size: 20, color: TEXT_MED, italics: true, font: "Calibri" }}),
        ]
      }}),
      new Paragraph({{
        spacing: {{ before: 0, after: 60 }},
        children: [new TextRun({{ text: "Dhirubhai Ambani University, India", size: 20, color: ACCENT, font: "Calibri", bold: true }})]
      }}),

      // TECHNICAL SKILLS
      sectionHeader("Technical Skills"),
      new Paragraph({{ spacing: {{ before: 80, after: 0 }}, children: [] }}),
      new Table({{
        width: {{ size: CONTENT_WIDTH, type: WidthType.DXA }},
        columnWidths: [2300, CONTENT_WIDTH - 2300],
        borders: {{
          top: {{ style: BorderStyle.NONE }}, bottom: {{ style: BorderStyle.NONE }},
          left: {{ style: BorderStyle.NONE }}, right: {{ style: BorderStyle.NONE }},
          insideH: {{ style: BorderStyle.NONE }}, insideV: {{ style: BorderStyle.NONE }}
        }},
        rows: [
          skillRow("Languages", "Python, SQL, Java, Bash, JavaScript"),
          skillRow("Big Data / ETL", "Apache Spark (PySpark), Kafka, Hive, Hadoop, Airflow, dbt, ETL/ELT pipeline design"),
          skillRow("GCP", "BigQuery, Dataproc, Dataflow, Cloud Composer, Pub/Sub, Cloud Storage"),
          skillRow("Databases & Stores", "PostgreSQL, MySQL, FAISS (vector DB), MongoDB, DynamoDB, Snowflake"),
          skillRow("Data Lakehouse", "Data modeling (star/snowflake schemas), lifecycle management, SLA ownership, schema design"),
          skillRow("AI / ML Infra", "OpenAI CLIP & BLIP (computer vision), NLP pipelines, semantic search, vector embeddings"),
          skillRow("APIs & Frameworks", "FastAPI, REST APIs, SQLAlchemy, async Python"),
          skillRow("DevOps", "Docker, Git, GitHub Actions, CI/CD, Linux/Bash scripting"),
          skillRow("Data Quality", "Anomaly detection, pipeline reliability, SLA monitoring, root-cause debugging"),
        ]
      }}),

    ]
  }}]
}});

Packer.toBuffer(doc).then(buffer => {{
  fs.writeFileSync("{output_docx_str}", buffer);
  console.log("✓ Resume written to {output_docx_str}");
}});
'''
    return script


# ── Output filename ────────────────────────────────────────────────────────────

def make_filename(job: dict) -> str:
    company = re.sub(r"[^a-zA-Z0-9]", "", job.get("company", "Company"))
    title   = re.sub(r"[^a-zA-Z0-9]", "", job.get("job_title", "Role"))
    stamp   = datetime.now().strftime("%Y%m%d")
    return f"JayDev_{company}_{title}_{stamp}.docx"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Customize Jay Dev's resume for a specific job URL."
    )
    parser.add_argument("--url", "-u", required=True,
                        help="Job posting URL to scrape and tailor the resume for.")
    parser.add_argument("--template", "-t", default=None,
                        help="Path to a template .docx (reserved for future use).")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("\n╔══════════════════════════════════════════════╗")
    print("║      Jay Dev  Resume Customizer              ║")
    print("╚══════════════════════════════════════════════╝\n")

    print("[1/4] Scraping job posting...")
    raw_text = scrape_job(args.url)
    if len(raw_text) < 100:
        print("  ERROR: Could not extract enough text from the job URL.")
        sys.exit(1)

    print("\n[2/4] Extracting job intelligence...")
    job = extract_job_info(raw_text, args.url)

    print("\n[3/4] Building tailored resume...")
    filename    = make_filename(job)
    output_docx = OUTPUT_DIR / filename
    tmp_js      = OUTPUT_DIR / f"_tmp_{filename}.js"

    js_code = build_resume_js(job, output_docx)
    tmp_js.write_text(js_code, encoding="utf-8")

    result = subprocess.run(
        ["node", str(tmp_js)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,  # <-- run from the script's directory, not customized_resumes/
    )
    tmp_js.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  ERROR generating .docx:\n{result.stderr}")
        sys.exit(1)

    print(f"  {result.stdout.strip()}")

    print(f"\n[4/4] Done!\n")
    print(f"  Company   : {job.get('company')}")
    print(f"  Role      : {job.get('job_title')}")
    print(f"  Location  : {job.get('location')}")
    print(f"  Output    : {output_docx}\n")

    if job.get("keywords"):
        print("  Top ATS keywords matched:")
        for kw in job["keywords"][:10]:
            print(f"    • {kw}")
    print()


if __name__ == "__main__":
    main()