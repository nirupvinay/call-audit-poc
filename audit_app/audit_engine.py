import json


SYSTEM_PROMPT = """
You are a deterministic transcript-grounded audit evaluator. You never guess. Every YES/FATAL requires quoted evidence. Absence of quotable evidence = NO.

PROCEDURE (mandatory, run in this order for every parameter)

STEP 1 — Decompose. Read the parameter text. List every distinct sub-requirement it contains as R1, R2, R3... (e.g. "business is regulated", "correct license identified", "whose name", "relative → declaration stated"). Do this before looking for evidence.

STEP 2 — Extract. For each Rn, scan the FULL transcript (not just the expected location) and pull:

exact quote (speaker tag + line/timestamp if available)
OR NOT FOUND Do not judge yet. Do not paraphrase the quote into a conclusion.

STEP 3 — Bind each answer to its own question. A customer/agent statement satisfies Rn only if it is a direct response to the specific sub-requirement Rn, not to a neighboring sub-requirement asked in the same exchange.

Example: agent asks "whose name is it in, and what's the address?" → customer answers "same address" → this satisfies the address sub-check ONLY. The name sub-check remains NOT FOUND unless answered separately.
Never let an answer to one sub-question fill a different sub-question just because they occurred in the same turn.

STEP 4 — Judge each Rn independently. Rn = YES only if: (a) evidence exists AND (b) it directly answers that specific Rn (per Step 3) AND (c) it is the final, non-retracted version if corrected later AND (d) it isn't reconstructed by you from surrounding context — the customer/agent must have actually said it. Otherwise Rn = NO.

STEP 5 — Reconcile identity where the parameter requires "whose name." When a parameter requires checking whose name a document/license is in:

Explicitly extract the name stated for the document.
Explicitly extract the name of the account/loan holder (from call opening).
Compare them. State match / mismatch / relationship (if stated) / unresolved.
If mismatch and no relationship is explicitly stated by a speaker → unresolved, not "assumed relative." Unresolved counts as failing any sub-check that depends on relationship being established.

STEP 6 — Apply logic exactly as written in the parameter.

AND: all Rn = YES → branch YES. Any Rn = NO → branch NO.
OR (branches): evaluate each full branch independently using Steps 1–5. If any one branch is fully YES → parameter YES. If all branches are NO → parameter NO. Do not mix evidence across branches.
FATAL: apply only if fatal=true is set on the parameter AND the outcome would otherwise be NO.

STEP 7 — Late-evidence sweep. Before finalizing a NO, re-scan the remainder of the transcript once for any later statement that completes a still-missing Rn (corrections, delayed answers, agent re-asking). If found, use it. If not, NO stands.

STEP 8 — Garbled/ambiguous evidence rule. If the only candidate evidence for a required YES is garbled, cut off, cross-talk, or supports two materially different readings that would flip the verdict → treat as NOT FOUND, not as a judgment call. Do not resolve garbled critical evidence toward the reading that completes the pattern. This applies with extra weight to code-mixed / regional-language / low-quality STT segments.

TRANSCRIPT RELIABILITY
STT errors are expected in names, numbers, business names, addresses, amounts.
Normalize a word only when (a) it's an isolated token, not a load-bearing fact, and (b) surrounding dialogue makes exactly one reading probable.
Never normalize in a way that manufactures the fact you need. If normalization would change the verdict, treat the original as uncertain → NO for that Rn.
Multiple languages/code-mixing/broken grammar: judge by meaning, not literal wording — but "meaning is clear" requires the same speaker or an immediate reply to have conveyed it, not your inference of what they probably meant.
SCOPE DISCIPLINE
Evaluate only what the current parameter's Rn list requires. Ignore correct-but-irrelevant conversation.
One parameter's conclusion never carries into another parameter.
No partial credit — a parameter with an AND condition and one missing Rn is NO in full, not "mostly yes.

Return only valid JSON in exactly the required format.

{
  "parameters": [
    {
      "name": "<exact parameter name>",
      "result": "YES | NO | FATAL",
      "reasoning": "<concise factual explanation with supporting evidence>",
      "timestamps": ["mm:ss"]
    }
  ]
}
""".strip()

class AuditResponseParseError(Exception):
    def __init__(self, raw_response: str):
        self.raw_response = raw_response
        super().__init__("AI returned unreadable JSON")


def build_audit_payload(templates: dict) -> list[dict]:
    audit_payload = []

    for template_name, template in templates.items():
        if not template.get("active"):
            continue

        for param in template["parameters"]:
            audit_payload.append(
                {
                    "template": template_name,
                    "name": param["title"],
                    "type": param["type"],
                    "fatal": param["fatal"],
                    "prompts": param["prompts"],
                    "logic": param["logic"],
                }
            )

    return audit_payload


def _extract_text_content(raw_content) -> str:
    if isinstance(raw_content, str):
        return raw_content

    if isinstance(raw_content, list):
        parts = []
        for item in raw_content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif item.get("type") == "output_text" and "text" in item:
                    parts.append(str(item["text"]))
        return "".join(parts)

    return str(raw_content)


def _safe_parse_json(raw_ai: str) -> dict:
    try:
        return json.loads(raw_ai)
    except Exception:
        start = raw_ai.find("{")
        end = raw_ai.rfind("}") + 1
        cleaned = raw_ai[start:end] if start != -1 and end > 0 else raw_ai
        try:
            return json.loads(cleaned)
        except Exception as exc:
            raise AuditResponseParseError(raw_ai) from exc


def _normalize_result(value: str, fatal: bool) -> str:
    value = (value or "").strip().upper()

    if value == "YES":
        return "YES"

    if value == "FATAL":
        return "FATAL" if fatal else "NO"

    if value == "NO":
        return "FATAL" if fatal else "NO"

    return "FATAL" if fatal else "NO"


def _normalize_timestamps(value) -> list[str]:
    if not isinstance(value, list):
        return []

    cleaned = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned.append(item.strip())
    return cleaned


def _default_missing_result(parameter: dict) -> dict:
    return {
        "name": parameter["name"],
        "result": "FATAL" if parameter.get("fatal") else "NO",
        "reasoning": "Required evidence was not clearly present.",
        "timestamps": [],
    }


def _reconcile_audit_response(parsed: dict, audit_payload: list[dict]) -> dict:
    ai_parameters = parsed.get("parameters", [])
    if not isinstance(ai_parameters, list):
        ai_parameters = []

    by_name = {}
    for item in ai_parameters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        if name not in by_name:
            by_name[name] = item

    final_parameters = []

    for parameter in audit_payload:
        expected_name = parameter["name"]
        raw_item = by_name.get(expected_name)

        if raw_item is None:
            final_parameters.append(_default_missing_result(parameter))
            continue

        final_parameters.append(
            {
                "name": expected_name,
                "result": _normalize_result(raw_item.get("result", ""), bool(parameter.get("fatal"))),
                "reasoning": str(raw_item.get("reasoning", "")).strip(),
                "timestamps": _normalize_timestamps(raw_item.get("timestamps", [])),
            }
        )

    return {"parameters": final_parameters}


def run_openai_audit(client, transcript: str, audit_payload: list[dict]) -> dict:
    response = client.chat.completions.create(
        model="gpt-5.6-terra",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "transcript": transcript,
                        "audit_parameters": audit_payload,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )

    raw_ai = _extract_text_content(response.choices[0].message.content)
    parsed = _safe_parse_json(raw_ai)
    return _reconcile_audit_response(parsed, audit_payload)


LEAD_CLASSIFIER_SYSTEM_PROMPT = """
You are a deterministic lead qualifier.

Classify the lead into exactly one category: HOT, WARM, or COLD, using only transcript evidence.

Rules:
1. Use only transcript evidence.
2. Never guess.
3. If there is clear buying intent, urgency, budget fit, and next-step readiness, prefer HOT.
4. If interest exists but commitment or clarity is partial, use WARM.
5. If weak or no interest, mismatch, or refusal, use COLD.
6. If uncertain, choose the lower-confidence category.

Return only valid JSON in this exact shape:

{
  "category": "HOT | WARM | COLD",
  "reasoning": "short factual explanation"
}
""".strip()


def run_openai_lead_classifier(client, transcript: str, output_requirement: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": LEAD_CLASSIFIER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "transcript": transcript,
                        "output_requirement": output_requirement,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )

    raw_ai = _extract_text_content(response.choices[0].message.content)
    parsed = _safe_parse_json(raw_ai)

    category = str(parsed.get("category", "")).strip().upper()
    if category not in {"HOT", "WARM", "COLD"}:
        category = "COLD"

    return {
        "category": category,
        "reasoning": str(parsed.get("reasoning", "")).strip(),
    }
