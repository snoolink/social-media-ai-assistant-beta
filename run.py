#!/usr/bin/env python3
"""
run.py - UI homepage for Suzy (AI Social Media Assistant) with streaming generation

This single-file Flask app demonstrates an elegant streaming UX for content generation:
- /api/generate-stream streams generated text chunks (simulated here)
- Frontend uses fetch stream reader and an AbortController to render progressive output
- Keeps the original non-streaming /api/strategy endpoint for convenience

Replace the simulated chunking in `stream_generate_post` with a real streaming AI backend
(e.g., OpenAI/other model streaming responses, or your streaming microservice).
"""
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ---- Placeholder AI / business logic functions ----
def generate_post(draft_text: str, platform: str, tone: str) -> str:
    """Non-streaming generator used for fallback/testing."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    generated = (
        f"[Suzy draft — {tone.title()} • {platform}] {draft_text.strip() or 'Share something interesting about your topic.'} "
        f"\n\nSuggested hashtags: #ai #social #suzy\nGenerated at: {now}"
    )
    return generated


def generate_strategy(topic: str, audience: str) -> dict:
    """Strategy helper (unchanged)."""
    suggestions = {
        "topic": topic,
        "audience": audience,
        "posting_frequency": "3x per week",
        "primary_goals": ["Grow awareness", "Drive traffic"],
        "recommended_content_types": ["Short videos", "Carousel posts", "How-to threads"],
        "quick_tips": [
            "Repurpose one long-form piece into 3 short posts.",
            "Post during local audience peak hours (mornings and evenings).",
        ],
    }
    return suggestions


def stream_generate_post(draft_text: str, platform: str, tone: str, schedule: str = None):
    """
    Simulate a streaming generator that yields chunks of text.
    Replace this with your model's streaming API (yield tokens/chunks as they arrive).
    """
    base = generate_post(draft_text, platform, tone)
    # Break into tokens (words) and stream them in small groups to mimic tokens
    tokens = base.split()
    chunk_size = 6
    for i in range(0, len(tokens), chunk_size):
        chunk = " ".join(tokens[i : i + chunk_size])
        # prefix to help client parse partial vs final (optional)
        yield chunk + (" " if not chunk.endswith("\n") else "")
        # simulate latency from a model streaming tokens
        time.sleep(0.08)

    # Optionally include scheduling preview as a final note
    if schedule:
        try:
            dt = datetime.fromisoformat(schedule)
            yield f"\n\nScheduled for: {dt.isoformat()}"
        except Exception:
            yield "\n\nNote: Could not parse scheduled time."

    # final marker (client doesn't strictly need this but it's explicit)
    yield "\n\n--end--"


# ---- Routes & UI ----
HOME_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Suzy — AI Social Media Assistant (Streaming)</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root{--bg:#071022;--card:#0b1220;--muted:#94a3b8;--accent:#7c3aed;--glass: rgba(255,255,255,0.03)}
    body{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial;background:linear-gradient(180deg,#071022 0%, #071827 100%);color:#e6eef8}
    .container{max-width:1100px;margin:32px auto;padding:24px}
    header{display:flex;align-items:center;gap:16px;margin-bottom:20px}
    .brand{display:flex;flex-direction:column}
    h1{margin:0;font-size:28px}
    p.lead{margin:4px 0 0;color:var(--muted)}
    .grid{display:grid;grid-template-columns:2fr 1fr;gap:18px}
    .card{background:var(--card);padding:18px;border-radius:12px;box-shadow:0 6px 18px rgba(2,6,23,0.6);border:1px solid rgba(255,255,255,0.03)}
    label{display:block;margin-top:12px;color:var(--muted);font-size:13px}
    textarea,input,select{width:100%;padding:10px;margin-top:6px;border-radius:8px;background:var(--glass);border:1px solid rgba(255,255,255,0.04);color:inherit;resize:vertical}
    button{background:var(--accent);color:white;padding:10px 14px;border-radius:10px;border:none;cursor:pointer;margin-top:12px}
    .muted{color:var(--muted);font-size:13px}
    .result{white-space:pre-wrap;margin-top:12px;padding:12px;border-radius:8px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.02);min-height:80px}
    .quick-actions{display:flex;gap:8px;flex-wrap:wrap}
    .chip{background:rgba(255,255,255,0.03);padding:8px 10px;border-radius:999px;font-size:13px;cursor:pointer;border:1px solid rgba(255,255,255,0.02)}
    footer{margin-top:18px;color:var(--muted);font-size:13px;text-align:center}
    .controls{display:flex;gap:8px;align-items:center}
    .tiny{font-size:12px;padding:6px 8px;border-radius:8px}
    @media(max-width:900px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div style="width:58px;height:58px;border-radius:12px;background:linear-gradient(135deg,#7c3aed,#06b6d4);display:flex;align-items:center;justify-content:center;font-weight:700">S</div>
      <div class="brand">
        <h1>Suzy — Your AI Social Media Assistant</h1>
        <p class="lead">Create smarter posts with streaming, progressive previews and instant feedback.</p>
      </div>
    </header>

    <div class="grid">
      <div>
        <div class="card">
          <h3>Compose a post (streaming preview)</h3>
          <p class="muted">Start generating and watch Suzy type the suggestion in real time.</p>

          <label>Draft text</label>
          <textarea id="draft" rows="5" placeholder="Write your idea or paste the key message..."></textarea>

          <div style="display:flex;gap:10px;margin-top:8px">
            <div style="flex:1">
              <label>Platform</label>
              <select id="platform">
                <option>Twitter / X</option>
                <option>LinkedIn</option>
                <option>Instagram</option>
                <option>Facebook</option>
                <option>TikTok</option>
              </select>
            </div>
            <div style="width:160px">
              <label>Tone</label>
              <select id="tone">
                <option>casual</option>
                <option>professional</option>
                <option>funny</option>
                <option>inspirational</option>
                <option>educational</option>
              </select>
            </div>
          </div>

          <label>Schedule (optional)</label>
          <input id="schedule" type="datetime-local" />

          <div class="controls" style="margin-top:8px">
            <button id="generateBtn">Generate (stream)</button>
            <button id="cancelBtn" class="tiny" style="display:none;background:#223037">Cancel</button>
            <div class="muted" id="genStatus"></div>
          </div>

          <div id="result" class="result" style="display:block"></div>
        </div>

        <div class="card" style="margin-top:14px">
          <h3>Strategy helper</h3>
          <p class="muted">Ask Suzy for a quick content strategy based on a topic and audience.</p>
          <label>Topic</label>
          <input id="strategyTopic" placeholder="e.g., product launch, newsletter growth" />
          <label>Audience</label>
          <input id="strategyAudience" placeholder="e.g., marketers, indie developers" />
          <button id="strategyBtn">Get strategy</button>
          <div id="strategyResult" class="result" style="display:none"></div>
        </div>
      </div>

      <aside>
        <div class="card">
          <h3>Quick actions</h3>
          <div class="quick-actions" style="margin-top:8px">
            <div class="chip" onclick="prefill('Announcing our new feature that will change how you work')">Announce feature</div>
            <div class="chip" onclick="prefill('Sharing lessons learned from a project')">Lessons learned</div>
            <div class="chip" onclick="prefill('Quick tip to help folks be more productive')">Quick tip</div>
            <div class="chip" onclick="prefill('How we improved our workflow with a tiny change')">Workflow story</div>
          </div>

          <h4 style="margin-top:14px">Recent drafts</h4>
          <div class="muted" style="margin-top:8px">No saved drafts yet. Suzy can autosave drafts and suggest improvements.</div>

          <h4 style="margin-top:14px">Integrations</h4>
          <div class="muted" style="margin-top:8px">Connect analytics & publishing platforms to unlock scheduling and performance insights.</div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button class="chip" style="flex:1" onclick="alert('Connect to Twitter/X (placeholder)')">Connect X</button>
            <button class="chip" style="flex:1" onclick="alert('Connect to Instagram (placeholder)')">Connect IG</button>
          </div>
        </div>

        <div class="card" style="margin-top:14px">
          <h3>Tips</h3>
          <ul class="muted" style="padding-left:18px">
            <li>Use content pillars to maintain variety.</li>
            <li>Repurpose long-form into multiple short posts.</li>
            <li>Test 2-3 posting times for your audience.</li>
          </ul>
        </div>
      </aside>
    </div>

    <footer>
      Built with ♥ for social creators. Streaming demo — replace simulated stream with your AI provider.
    </footer>
  </div>

<script>
function prefill(text){
  document.getElementById('draft').value = text;
  window.scrollTo({top:0,behavior:'smooth'});
}

let controller = null;
document.getElementById('generateBtn').addEventListener('click', () => {
  const draft = document.getElementById('draft').value;
  const platform = document.getElementById('platform').value;
  const tone = document.getElementById('tone').value;
  const schedule = document.getElementById('schedule').value;

  // Abort previous streaming if any
  if (controller) {
    controller.abort();
    controller = null;
  }

  controller = new AbortController();
  const signal = controller.signal;

  document.getElementById('genStatus').textContent = 'Streaming...';
  document.getElementById('result').textContent = '';
  document.getElementById('cancelBtn').style.display = 'inline-block';

  fetch('/api/generate-stream', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({draft, platform, tone, schedule}),
    signal
  }).then(async resp => {
    if (!resp.ok) {
      document.getElementById('genStatus').textContent = 'Error: ' + resp.statusText;
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    try {
      while (!done) {
        const { value, done: streamDone } = await reader.read();
        done = streamDone;
        if (value) {
          const chunk = decoder.decode(value, {stream: true});
          // append chunk progressively
          const out = document.getElementById('result');
          out.textContent += chunk;
          // maintain scroll to bottom of result for long content
          out.scrollTop = out.scrollHeight;
        }
      }
      document.getElementById('genStatus').textContent = '';
    } catch (err) {
      if (err.name === 'AbortError') {
        document.getElementById('genStatus').textContent = 'Streaming aborted';
      } else {
        document.getElementById('genStatus').textContent = 'Stream error';
        console.error(err);
      }
    } finally {
      document.getElementById('cancelBtn').style.display = 'none';
      controller = null;
    }
  }).catch(err => {
    if (err.name === 'AbortError') {
      document.getElementById('genStatus').textContent = 'Streaming aborted';
    } else {
      document.getElementById('genStatus').textContent = 'Network error';
      console.error(err);
    }
    document.getElementById('cancelBtn').style.display = 'none';
    controller = null;
  });
});

document.getElementById('cancelBtn').addEventListener('click', () => {
  if (controller) {
    controller.abort();
  }
});

// Strategy button (unchanged behavior)
document.getElementById('strategyBtn').addEventListener('click', async () => {
  const topic = document.getElementById('strategyTopic').value;
  const audience = document.getElementById('strategyAudience').value;
  const out = document.getElementById('strategyResult');
  out.style.display = 'none';
  out.textContent = '';
  try {
    const resp = await fetch('/api/strategy', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({topic, audience})
    });
    const data = await resp.json();
    out.style.display = 'block';
    out.textContent = JSON.stringify(data, null, 2);
  } catch(err){
    out.style.display = 'block';
    out.textContent = 'Error fetching strategy';
    console.error(err);
  }
});
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HOME_HTML)


@app.route("/api/generate-stream", methods=["POST"])
def api_generate_stream():
    """
    Streaming endpoint that returns a text/plain streaming response.
    Body (JSON):
    { "draft": "...", "platform": "Instagram", "tone": "casual", "schedule": "2025-11-05T14:00" }

    The response is a chunked plain text stream. The client progressively reads and renders chunks.
    """
    data = request.get_json() or {}
    draft = data.get("draft", "")
    platform = data.get("platform", "General")
    tone = data.get("tone", "casual")
    schedule = data.get("schedule")

    # Use stream_with_context to ensure request context is available during iteration
    generator = stream_generate_post(draft, platform, tone, schedule)
    return Response(stream_with_context(generator), mimetype="text/plain; charset=utf-8")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Non-streaming fallback. Returns the full generated text in JSON.
    """
    data = request.get_json() or {}
    draft = data.get("draft", "")
    platform = data.get("platform", "General")
    tone = data.get("tone", "casual")
    schedule = data.get("schedule")

    generated_text = generate_post(draft, platform, tone)
    if schedule:
        try:
            parsed = datetime.fromisoformat(schedule)
            generated_text += f"\n\nScheduled for: {parsed.isoformat()}"
        except Exception:
            generated_text += "\n\nNote: Could not parse scheduled time."

    return jsonify({"generated": generated_text})


@app.route("/api/strategy", methods=["POST"])
def api_strategy():
    data = request.get_json() or {}
    topic = data.get("topic", "general")
    audience = data.get("audience", "everyone")
    result = generate_strategy(topic, audience)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") not in ("0", "false", "False")
    print(f"Starting Suzy streaming UI on http://0.0.0.0:{port}  (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)