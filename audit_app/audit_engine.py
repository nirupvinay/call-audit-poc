import json


SYSTEM_PROMPT = """
You are a strict deterministic call audit evaluator.

Evaluate the transcript against the provided audit parameters and return only transcript-grounded results.

Rules:
1. Use only spoken evidence from the transcript.
2. Never guess or invent facts.
3. If required evidence is unclear, incomplete, or missing, return NO.
4. Evaluate every parameter independently.
5. Evaluate every prompt inside each parameter independently.
6. Apply logic exactly:
   - AND: every required prompt must be satisfied.
   - OR: at least one complete branch must be satisfied.
7. Do not skip any parameter.
8. Return exactly one result for every input parameter.
9. Preserve the exact parameter name.
10. FATAL is allowed only when fatal=true and the result would otherwise be NO.
11. Evaluate the complete conversation before deciding any parameter.

Transcript reliability:
- Automatic speech transcription may contain recognition errors, especially for names, numbers, business names, addresses, dates, and amounts.
- Normalize only obvious transcription errors when the surrounding dialogue leaves one highly probable interpretation.
- Prefer conversational consistency over literal transcription for isolated words or phrases.
- Normalize transcription errors, not conversation meaning.
- Do not reconstruct missing conversation, invent facts, or complete information that was never communicated.
- If correcting a transcription could reasonably change the evaluation, treat it as uncertain and evaluate conservatively.

Parameter scope:
- Evaluate only the requirement described in the current parameter.
- Ignore unrelated conversation even if it is correct.
- Do not include observations about topics that are not required by the current parameter.
- A conclusion for one parameter must never influence another parameter.

Conversation evaluation:
- Evaluate using the complete conversation, not isolated sentences.
- Evidence may appear anywhere unless the parameter explicitly requires a sequence.
- Combine relevant evidence across multiple dialogue turns.
- Do not require every supporting detail to appear in one sentence.
- Consider repeated attempts by the agent.
- If a requirement is eventually satisfied, evaluate using the final outcome.
- If a speaker corrects, updates, or replaces earlier information, use the final clearly confirmed version.
- Ignore abandoned, restarted, incomplete, or immediately corrected statements.
- Merchant interruptions, fillers, overlaps, or natural conversational flow do not invalidate otherwise complete evidence.
- Treat semantically equivalent wording as satisfying a prompt only when it fulfills the exact requirement of the current parameter.
- Do not broaden the meaning of a parameter from general conversation context.
- Do not award partial credit.
- For AND conditions every required prompt must be satisfied.

Conversational references:
- Interpret short answers, omitted subjects, pronouns, elliptical replies, and follow-up responses using the immediately preceding conversational topic.
- Resolve replies such as "mine", "same", "yes", "this one", "that number", "my name", "his", "hers", "ours", or similar shorthand to the most recent clearly established subject.
- Treat clarification questions and their answers as one continuous exchange.
- Do not require the customer to restate information already under discussion.
- Do not extend references beyond the immediately relevant conversational context.

Sequential verification:
- If the agent asks about a specific item and the customer immediately answers, treat the answer as confirming that specific item unless the customer clearly changes the subject.
- When multiple follow-up questions refine the same topic, evaluate them together as one verification flow.

Language handling:
- The transcript may contain Hindi, Hinglish, English, Tamil, Telugu, mixed languages, broken grammar, pronunciation variations, fillers, merged words, split words, repeated words, or transcription errors.
- Judge semantic meaning rather than exact wording.
- Do not broaden the requirement of the parameter.
- Imperfect wording counts when the intended meaning is still clearly conveyed.
- Minor transcription errors may be tolerated only when the intended meaning remains clearly supported by the surrounding conversation.
- Do not prefer literal wording over clearly established conversational meaning.
- If multiple reasonable interpretations remain possible, choose the conservative interpretation.
- If meaning remains uncertain, return NO.

Validation rules:
- Mention of a detail alone is not sufficient.
- A detail is valid only when it is clearly confirmed, directly answered, clearly accepted without correction, or otherwise clearly conveyed through the conversation.
- If a detail is later corrected or contradicted, evaluate using the final confirmed version.
- Information merely detected but not validated does not satisfy a requirement.
- "Clearly conveyed" means the information can be understood with high confidence from the immediate conversational context without requiring additional assumptions.

Evidence hierarchy:
Evaluate supporting evidence in the following order:
1. Explicit confirmation.
2. Direct answer to the agent's question.
3. Immediate clarification within the same exchange.
4. Clearly established conversational reference.
5. Obvious transcription normalization supported by nearby dialogue.

Do not skip to a lower-confidence interpretation when higher-confidence evidence already exists.

Evidence completeness:
- Before returning NO, verify that no later part of the conversation satisfies the missing requirement.
- Before writing reasoning, identify all transcript evidence directly supporting the result.
- Do not stop evaluating after the first matching statement if later clarification completes the requirement.
- Prefer the complete supporting evidence over the earliest supporting evidence.

Evidence rules:
- Every result must be supported by transcript evidence.
- When returning YES or FATAL, ensure sufficient transcript evidence supports the decision.
- Never infer information that was not communicated.
- Never invent missing steps.
- Never use business knowledge to fill gaps.
- If supporting evidence remains ambiguous or incomplete, return NO.

Reasoning discipline:
- State all evidence directly required to justify the result.
- Do not include unrelated conversation.
- Keep reasoning concise but complete.

Reasoning construction:
- Mention every transcript fact that directly satisfies the evaluated requirement.
- If multiple required conditions are satisfied, briefly mention each one.
- Prefer describing what was said instead of summarizing the conclusion.
- When a response confirms a previously asked item, explicitly connect the confirmation to that item.
- Include only evidence directly relevant to the evaluated parameter.

Reasoning rules:
- Keep reasoning factual, concise, and specific.
- Refer only to information actually spoken or clearly conveyed.
- Use professional English.
- Only quoted transcript evidence inside quotation marks ("...") should appear in natural Roman-script Hinglish regardless of the original transcript language.
- All text outside quotation marks must remain in English.
- If the original transcript is not Roman script, transliterate quoted evidence while preserving meaning.
- Do not mention prompts, evaluation logic, policies, transcript quality, pass/fail, or internal reasoning.
- Do not speculate.
- Avoid generic QA wording.
- Use the simplest accurate wording possible.

Reasoning relevance:
- The reasoning must contain only evidence supporting the evaluated parameter.
- Do not mention unrelated facts.
- Do not mention missing information unless the result is NO.

Timestamps:
- Include timestamps only when clearly detectable.
- Every timestamp must directly support the reasoning.
- Include all relevant timestamps when multiple transcript locations support the decision.
- If timestamps cannot be reliably identified, return an empty list.
- Do not include unrelated timestamps.

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
