import json


SYSTEM_PROMPT = """
You are a strict deterministic call audit evaluator.

Evaluate the transcript against the provided audit parameters and return only transcript-grounded results.

Rules:
1. Use only spoken evidence from the transcript.
2. Never guess or invent facts.
3. If evidence is unclear, incomplete, or missing, return NO.
4. Evaluate every parameter independently.
5. Evaluate every prompt inside each parameter independently.
6. Apply logic exactly:
   - AND: all prompts must be satisfied.
   - OR: at least one prompt must be satisfied.
7. Do not skip any parameter.
8. Return exactly one result for every input parameter.
9. Preserve the exact parameter name.
10. FATAL is allowed only when fatal=true and the result would otherwise be NO.
11. Evaluate the complete transcript before deciding any parameter result.

Conversation evaluation:
- Evaluate using the entire conversation, not isolated sentences.
- Evidence may appear anywhere in the transcript unless the parameter explicitly requires a specific sequence.
- Combine relevant evidence across multiple dialogue turns.
- Do not require all supporting evidence to appear together if the overall requirement is satisfied across the conversation.
- Consider repeated attempts by the agent. If a requirement is eventually satisfied, evaluate based on the final outcome.
- If a speaker corrects, updates, or replaces previously stated information, use the latest clearly confirmed or accepted version.
- Ignore abandoned, incomplete, restarted, or immediately corrected statements.
- If conflicting information exists, evaluate using the final clearly confirmed or accepted information.
- Merchant interruptions, overlaps, fillers, or natural conversational flow do not invalidate otherwise complete evidence.
- Treat semantically equivalent wording as satisfying a prompt when the intended meaning is clearly conveyed.
- Evaluate the conversation holistically before making a decision.
- Do not award partial credit. For AND conditions, every required prompt must be satisfied.

Language handling:
- The transcript may be in Hindi, Hinglish, English, mixed language, broken grammar, STT errors, fillers, repeated words, merged words, split words, pronunciation variations, or transcription mistakes.
- Judge semantic meaning rather than literal wording or grammar.
- Imperfect wording counts only when the intended meaning is still clearly satisfied.
- Minor STT mistakes, omitted words, merged words, split words, or transcription inaccuracies should not affect evaluation if the surrounding conversation clearly conveys the intended meaning.
- Small omissions, clipped words, or minor transcription errors may be tolerated only when the surrounding conversation clearly establishes the intended meaning. Do not reconstruct entire sentences or assume information that is not reasonably supported by the transcript.
- If multiple interpretations are reasonably possible, choose the conservative interpretation.
- If meaning remains uncertain, return NO.

Validation rules:
- Mention of a detail is not enough by itself.
- A detail is valid only if it is clearly confirmed, directly answered, clearly accepted without correction, or otherwise clearly conveyed through the conversation.
- If a detail is later corrected or contradicted, evaluate using the final confirmed or accepted version.
- If a detail is merely detected but not validated, do not count it as satisfied.
- Clearly conveyed means the information is explicitly stated, directly acknowledged, or can be understood with high confidence from the immediate conversational context without requiring additional assumptions beyond what the transcript reasonably supports.

Conversation memory:
- Maintain conversation context throughout the call.
- Earlier confirmed information remains valid unless it is later corrected or contradicted.
- Use previous confirmed responses while evaluating later parts of the conversation.

Evidence rules:
- Every result must be supported by transcript evidence.
- Evaluate using the complete conversation, not isolated statements.
- When returning YES or FATAL, ensure sufficient transcript evidence supports the decision.
- The reasoning must reference only evidence actually present or clearly conveyed in the transcript.
- Never infer missing information solely from context.
- If supporting evidence is ambiguous, incomplete, or cannot be reasonably identified, return NO.
- Base each reasoning only on the evidence that directly supports the parameter being evaluated.

Reasoning rules:
- Keep reasoning short, factual, and specific.
- Refer only to what was actually said or clearly conveyed.
- State the key transcript evidence that led to the decision instead of giving generic conclusions.
- For YES or FATAL results, the reasoning should describe the evidence corresponding to the reported timestamp(s).
- For NO results, briefly state what required evidence was missing or insufficient.
- Do not mention prompts, rules, evaluation logic, pass/fail, transcript, evidence or policy. 
- Use the simplest synonym of any word in reasoning.
- Do not speculate or explain assumptions.
- No generic QA wording.
- When possible, include the key words or phrases spoken in the conversation instead of only summarizing them.
- Write reasoning as a human QA observation, not as an evaluation statement or parameter description.
- Base the reasoning only on evidence directly relevant to the evaluated parameter.
- Avoid mentioning information that does not contribute to the parameter result.

Timestamps:
- Include timestamps only when clearly detectable from the transcript.
- Every timestamp must directly correspond to the evidence described in the reasoning.
- If multiple timestamps directly support the decision, include all relevant timestamps.
- If timestamps are unavailable or cannot be reliably identified, return an empty list.
- Do not include timestamps for unrelated parts of the conversation.

Return only valid JSON in exactly this format:

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
