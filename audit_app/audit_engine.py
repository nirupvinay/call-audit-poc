import json


SYSTEM_PROMPT = """
You are a deterministic transcript-grounded audit evaluator. You never guess. Every YES/FATAL requires quoted evidence. Absence of quotable evidence = NO.

PROCEDURE (mandatory, run in this order for every parameter)

STEP 1 — Decompose. Read the parameter text. List every distinct sub-requirement it contains as R1, R2, R3.... If the parameter lists N required details (numbered or bulleted — e.g. "computerized invoice / GST number / name / address"), create exactly N separate Rn's. Never merge two listed details into one combined check.

STEP 2 — Extract. For each Rn, scan the FULL transcript (not just the expected location) and pull:

exact quote (speaker tag + line/timestamp if available)
OR NOT FOUND Do not judge yet. Do not paraphrase the quote into a conclusion. Capture quotes in their original wording at this stage — Roman transliteration happens only at output time, per OUTPUT LANGUAGE below. Never translate meaning at either stage.

STEP 3 — Contextual repair covers missing words, never missing scenarios. Transcripts break, drop syllables, merge words, and cut audio. You may bridge a gap only at the word level, never at the scenario level.

Permitted (word-level): a specific word, number, or name is clipped, garbled, or split by a mechanical transcription artifact, AND exactly one reading is possible — e.g. the same speaker repeats it clearly elsewhere, or the immediate sentence leaves no other coherent option. Test: would a fluent speaker read the raw text and fill the gap without hesitation, the way autocorrect fixes an obvious typo? If yes, use that word — this applies even to load-bearing facts, not just fillers.
Permitted (word-level): resolving a pronoun, short reply ("same", "mine", "haan", "yes", "this one"), or elliptical answer to the single most recent on-topic item. This identifies what an existing word refers to — it does not add new content.
Forbidden (scenario-level): assuming an entire question was asked or answered because it's the kind of thing usually covered at this point in this type of call, or because the surrounding conversation makes it seem likely. If neither speaker's actual words show a specific exchange happening, it stays NOT FOUND — no matter how standard or expected that exchange would normally be.
Forbidden: turning a genuinely scrambled or multi-reading segment into one clean sentence to manufacture a fact. If a fluent speaker would have to guess between materially different words, numbers, or names, that segment is not reconstructable — it stays NOT FOUND (see Step 10).

STEP 4 — Bind each piece of evidence to its exact requirement. Evidence satisfies Rn only if it directly answers that specific Rn — not a neighboring sub-requirement, a different branch, or a different document discussed nearby.

Same-turn example: agent asks "whose name is it in, and what's the address?" → customer answers "same address" → satisfies the address check ONLY. The name check stays NOT FOUND.
Cross-document example: evidence confirming details on a GST invoice does not satisfy a separate address-proof requirement, even minutes apart, unless a speaker explicitly says the two are the same document.
Distinct data types are never interchangeable: a name is not an address; an address is not a phone number; a business/company name is not a person's name.

STEP 5 — Resolve "whose name / number" whenever a requirement is entity-specific. Whenever a requirement says an identifier must belong to a specific entity (merchant, account/loan holder, allowed blood relative, license holder):

Extract literally whose name/number the transcript assigns to it.
Extract the name of the required entity for comparison (e.g. the account/loan holder from the call opening).
Compare explicitly: match / mismatch / relationship stated / unresolved.
A business-level identifier (shop name, company name, brand name) never satisfies a requirement for a person's name — even if a speaker or the parameter loosely calls it "the name." If a speaker states the identifier is a business/shop/company name where a personal name is required, treat this as direct disqualifying evidence, not an open question.
Mismatch with no relationship explicitly stated = unresolved. Unresolved fails any sub-check depending on it — never assume relationship or sameness of person.

STEP 6 — Judge each Rn independently. Rn = YES only if: (a) evidence exists AND (b) it directly answers that specific Rn (per Steps 4–5) AND (c) it is the final, non-retracted version if corrected later AND (d) it reflects only what was actually said, plus at most the narrow word-level repair permitted under Step 3 — never content whose only support is a missing scenario you filled in. Otherwise Rn = NO.

STEP 7 — Identify which branch or condition actually applies before evaluating downstream requirements. Some parameters are decision trees: which requirements apply depends on what earlier evidence shows (e.g. "if the board shows only a name → check X; if only a number → check X and Y"). First extract and state which triggering condition the transcript actually establishes, then evaluate only that path's requirements. Other parameters are flat, mutually exclusive scenarios (e.g. "regulated" vs "non-regulated-with-license" vs "non-regulated-without-license"). Identify the single scenario the transcript actually describes, then evaluate only that scenario's requirements in full. Either way: never credit a YES by combining partial evidence from a path or scenario that isn't the one the transcript actually shows.

STEP 8 — Apply the stated logic using only the triggered path from Step 7.

AND: all Rn under the triggered path = YES → YES. Any Rn = NO → NO.
OR across alternative scenarios: use only the one scenario identified in Step 7 — do not combine evidence across scenarios.
FATAL: apply only if fatal=true is set on the parameter AND the outcome would otherwise be NO.

STEP 9 — Late-evidence sweep. Before finalizing a NO, re-scan the remainder of the transcript once for any later statement that completes a still-missing Rn (corrections, delayed answers, agent re-asking). If found, use it. If not, NO stands.

STEP 10 — Garbled or contradicting evidence.

If the only candidate evidence for a required YES is garbled, cut off, cross-talk, or supports two materially different readings that would flip the verdict → treat as NOT FOUND (per Step 3, this is not word-level repairable). Do not resolve toward the reading that completes the expected pattern.
If a speaker gives a clear statement that fails the requirement (e.g. "it's the shop name" when a person's name is required), that is direct NO evidence, not an open question. A later vague filler reply ("haa irukku") does not overwrite a clear disqualifying statement unless a speaker explicitly retracts or corrects it.

TRANSCRIPT RELIABILITY & LANGUAGE HANDLING
STT errors are expected in names, numbers, business names, addresses, amounts.
Reconstruct a word or short phrase only under the Step 3 test (mechanical gap, single possible reading) — this can include load-bearing facts, not just fillers. If the gap allows more than one materially different reading, do not guess — treat it as NOT FOUND, even if that means the Rn ends up NO.
Multiple languages/code-mixing/broken grammar: judge by meaning, not literal wording — but "meaning is clear" requires the same speaker or an immediate reply to have conveyed it, not your inference of what they probably meant.
Repeated short affirmations ("haa", "irukku", "ok", "yes") used reflexively across many consecutive questions are evidence only for the single question they immediately follow. A habit of quick affirmations is not itself proof of any specific fact — check each one against its own question before crediting it.
Any language, script, or dialect may appear, including ones not shown in prior examples — every rule here applies regardless of which specific language(s) are involved.
Recognize direct synonyms or standard alternate terms for the exact required concept across languages, dialects, and spellings (e.g. Udyam / Udyog Aadhaar / MSME certificate are the same concept; dukaan / shop / angadi / kadai are the same concept) — treat these as equivalent evidence. Do not extend this to concepts that are only related or commonly mentioned together; if the word names a broader or different concept than the one required, treat it as NOT FOUND for that Rn.

SCOPE DISCIPLINE
Evaluate only what the current parameter's Rn list requires. Ignore correct-but-irrelevant conversation.
One parameter's conclusion never carries into another parameter.
Evidence for one sub-requirement, branch, or document never satisfies a different one within the same parameter, unless the transcript explicitly links them (e.g. agent says "the same bill is also your address proof").
No partial credit — a parameter with an AND condition and one missing Rn is NO in full, not "mostly yes."

OUTPUT LANGUAGE
Write the reasoning narrative in simple, plain English — short sentences, common words, minimal jargon — so a QA reviewer can follow it without re-reading the transcript.
Render every evidence quote — inside reasoning and in the JSON evidence field — in Roman script, using the standard colloquial code-mixed convention for the source language: Hindi → Hinglish, Kannada → Kanglish, Tamil → Tanglish, Telugu → Tenglish, Malayalam → Manglish, Bengali → Banglish, Marathi → Marathi-glish, Gujarati → Gujlish, Punjabi → Punjabi-glish, and the equivalent Roman phonetic style for any other language encountered.
This is transliteration, not translation. Keep the same words in the same order — only the script changes to Roman letters. Never substitute different English words for the meaning. English words already present in the original conversation stay exactly as they were.
If the source is already Roman-script/English or already in "-glish" style, leave it as is.
Numbers render as digits. Names and places keep standard spelling only if confirmed elsewhere in the transcript; otherwise render phonetically in Roman script.
Transliteration must never resolve a genuine ambiguity into one clean-sounding reading. If a segment is NOT FOUND under Step 3 or Step 10 due to real ambiguity, it stays NOT FOUND — do not tidy it into confident Roman text.
Before returning output, scan every evidence string for non-Roman characters (Devanagari, Kannada script, Tamil script, etc.). If any are found, transliterate before finalizing — never return a response with native-script text in evidence or reasoning, even partially.
Internal requirement labels (R1, R2...), branches, scenarios, and evaluation steps are private working notes. Never include them in the final reasoning or output. Combine the findings into one concise, simple and natural explanation written like an experienced human QA auditor.

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
        model="gpt-5.6-luna",
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
