# Resume Customizer CLI

Automatically tailors **Jay Dev's** resume to any job posting by scraping the job URL, analyzing it with Claude AI, and generating a polished `.docx` file in the `customized_resumes/` folder.

---

## Setup

### 1. Install Python dependencies

```bash
pip install requests beautifulsoup4 anthropic
```

### 2. Install Node.js dependency (for .docx generation)

```bash
npm install -g docx
```

### 3. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Usage

```bash
python customize_resume.py --url "https://jobs.example.com/senior-data-engineer-123"
```

### Optional flags

| Flag | Description |
|------|-------------|
| `--url` / `-u` | **(Required)** Job posting URL |
| `--template` / `-t` | Reserved for future use (template is embedded) |

---

## What it does

| Step | Action |
|------|--------|
| 1 | Scrapes the job posting URL (with fallback to Claude web search) |
| 2 | Sends the text to Claude to extract: job title, company, location, responsibilities, skills, ATS keywords |
| 3 | Claude rewrites all work experience bullets to match the job description vocabulary |
| 4 | Generates a branded `.docx` resume with updated location and tailored content |

---

## Output

Resumes are saved to `customized_resumes/` with the naming pattern:

```
JayDev_<Company>_<Role>_<YYYYMMDD>.docx
```

**Example:**
```
customized_resumes/JayDev_Yahoo_SeniorDataEngineer_20260427.docx
```

---

## What changes per resume

- **Location in header** updated to match the job's city/state
- **Professional Summary** rewritten to mirror the JD's language and priorities
- **All work experience bullets** adapted to emphasize skills relevant to the role
- **Snoolink project bullets** reframed to highlight whichever aspects matter most
- **ATS keywords** from the JD woven into bullet language

## What stays constant

- Your name, contact info, LinkedIn, GitHub
- All factual details (companies, dates, technologies you actually used)
- Education section
- Technical Skills section
- Formatting and design

---

## Troubleshooting

**"Could not extract enough text"** — Some job boards (Workday, Greenhouse) block scrapers. Try copying the job description text into a `.txt` file and adapting the script to read from file instead.

**Node.js errors** — Make sure `docx` is installed globally: `npm install -g docx`

**API key errors** — Make sure `ANTHROPIC_API_KEY` is set in your environment.