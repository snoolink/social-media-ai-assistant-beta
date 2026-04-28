"""
LinkedIn Connection Note Generator using Amazon Bedrock
Reads INPUT_CSV, generates a personalized connection note for each row
using the 'headline' and 'about' columns, and writes results to OUTPUT_CSV.
Saves progress to the output CSV after every single row.
"""

import boto3
import pandas as pd
import json
import time
from pathlib import Path


# ── Config — edit these values ────────────────────────────────────────────────
INPUT_CSV  = "linkedin_profiles/extracted_profiles_keydata_04-27-26-18.csv"
OUTPUT_CSV = "linkedin_profiles/extracted_profiles_keydata_04-27-26-18_with_notes.csv"

MODEL_ID       = "google.gemma-3-12b-it"  # Bedrock model ID
AWS_REGION     = "us-east-1"   # Your AWS region
MAX_NOTE_CHARS = 300            # LinkedIn connection note hard limit
RETRY_ATTEMPTS = 3
RETRY_DELAY    = 2              # seconds between retries
OVERWRITE      = False          # Set True to regenerate notes that already exist
# ─────────────────────────────────────────────────────────────────────────────


def build_prompt(row: pd.Series) -> str:
    """Build a prompt using headline and about columns."""
    name     = str(row.get("name", "")).strip()
    headline = str(row.get("headline", "")).strip()
    about    = str(row.get("about", "")).strip()[:800]  # truncate very long bios

    # Extract first name only
    first_name = name.split()[0] if name else "there"

    context_parts = []
    if headline: context_parts.append(f"Headline: {headline}")
    if about:    context_parts.append(f"About: {about}")

    context = "\n".join(context_parts)

    return f"""You are writing a LinkedIn connection request note on behalf of Jay, a Data Engineer with 5 years of experience building scalable data pipelines across cloud and modern data stacks.

The recipient's first name is: {first_name}

Their profile:
{context}

---

Write a warm, friendly, and slightly tech-oriented LinkedIn connection note following these rules:

TONE & INTENT:
- Friendly and genuine — not salesy or robotic
- Show real curiosity about a specific niche, tool, domain, or challenge mentioned in their headline or about section that overlaps with data engineering (e.g. data infrastructure, analytics, pipelines, cloud, ML, fintech data, healthcare data, etc.)
- Indirectly hint that Jay is open to opportunities — do NOT ask for a job directly. Instead phrase it as "exploring if there's an alignment" or "seeing if there's a fit" or "curious if your team is growing"
- The note should feel like it's from a real person, not a template
- Do not use any emojies, or -. Use just text

FORMAT — output EXACTLY this structure with these exact line breaks and spacing:
Hi [first name],

[: couple of warm, specific observation about something in their profile — their domain, tech stack, industry focus, or a challenge they work on. Tie it your data engineering naturally and express interest in connecting and talking in detail. It should be less than 250 characters and feel personalized to their profile, not generic.]

Regards,
Jay

STRICT RULES:
- Total output must be under {MAX_NOTE_CHARS} characters
- Preserve the blank lines between paragraphs exactly as shown above
- Do NOT use "Dear", do NOT use hollow phrases like "Hope you're doing well"
- Do NOT mention any specific company name or job title that wasn't in the profile
- Return ONLY the final note text — no explanations, no labels, no markdown
- Return a complete note which is less than {MAX_NOTE_CHARS} characters. If you can't fit a complete note in that limit, change the content to fit.

Connection note:"""


def call_bedrock(client, prompt: str) -> str:
    """
    Call Bedrock and return the generated note.
    Uses invoke_model with the Messages API format.
    Handles different provider response schemas.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_new_tokens": 300,
                "temperature": 0.7,
            })

            response = client.invoke_model(
                modelId=MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=body,
            )

            raw = json.loads(response["body"].read())

            # ── Parse response — handle different provider schemas ──────────
            note = ""
            if "outputs" in raw:
                note = raw["outputs"][0].get("text", "")
            elif "choices" in raw:
                note = raw["choices"][0].get("message", {}).get("content", "") \
                    or raw["choices"][0].get("text", "")
            elif "content" in raw:
                note = raw["content"][0].get("text", "")
            elif "text" in raw:
                note = raw["text"]
            else:
                print(f"  ⚠️  Unexpected response schema: {list(raw.keys())}")
                note = str(raw)

            note = note.strip()

            # Enforce hard character limit, trimming at a word boundary
            if len(note) > MAX_NOTE_CHARS:
                note = note[:MAX_NOTE_CHARS].rsplit(" ", 1)[0]

            return note

        except Exception as e:
            print(f"  Attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY)
            else:
                print(f"  Skipping row after {RETRY_ATTEMPTS} failed attempts.")
                return ""


def save_progress(df: pd.DataFrame):
    """Save the current dataframe to OUTPUT_CSV immediately."""
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)


def main():
    if not Path(INPUT_CSV).exists():
        print(f"❌  Input file not found: {INPUT_CSV}")
        return

    # If output already exists, resume from it to preserve prior progress
    if Path(OUTPUT_CSV).exists():
        print(f"\n📂  Resuming from existing output: {OUTPUT_CSV}")
        df = pd.read_csv(OUTPUT_CSV)
    else:
        print(f"\n📂  Reading: {INPUT_CSV}")
        df = pd.read_csv(INPUT_CSV)

    if "connection_note" not in df.columns:
        df["connection_note"] = ""

    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    total   = len(df)

    print(f"🔢  Total rows: {total}")
    print(f"🤖  Model: {MODEL_ID}\n")

    for idx, row in df.iterrows():
        existing = str(row.get("connection_note", "")).strip()
        if existing and existing.lower() != "nan" and not OVERWRITE:
            print(f"[{idx+1}/{total}] ⏭  Skipping (note exists): {row.get('name', idx)}")
            continue

        name = row.get("name", f"Row {idx}")
        print(f"[{idx+1}/{total}] ✍️  Generating note for: {name}")

        note = call_bedrock(bedrock, build_prompt(row))

        if note:
            df.at[idx, "connection_note"] = note
            # Print preview with actual line breaks visible
            preview = note[:120].replace("\n", "↵")
            print(f"         → ({len(note)} chars) {preview}{'…' if len(note) > 120 else ''}")
        else:
            print("         → ⚠️  No note generated.")

        # 💾 Save after every row so no progress is lost on interruption
        save_progress(df)

        time.sleep(0.5)  # gentle rate limiting

    print(f"\n✅  Done! Output saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()