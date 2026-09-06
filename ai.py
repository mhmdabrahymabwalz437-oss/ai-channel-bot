import json
import requests

SYSTEM = """أنت محرر محتوى عربي محترف. أنشئ منشورا أصليا مفيدا اعتمادا على البرومبت والمصادر. لا تنسخ النصوص. اذكر المصدر في آخر الكابشن. أخرج JSON فقط."""


def _parse_json(content: str) -> dict:
    cleaned = content.strip().replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    if start >= 0:
        cleaned = cleaned[start:]
    return json.loads(cleaned)


def generate(prompt: str, items, api_key: str, base_url: str, model: str) -> dict:
    sources = "\n".join(f"- {x.title}: {x.summary[:500]} ({x.url})" for x in items)
    request = dict(
        model=model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"البرومبت: {prompt}\nالمصادر:\n{sources}"}],
        response_format={"type": "json_object"},
    )
    if "generativelanguage.googleapis.com" in base_url:
        request["max_tokens"] = 2000
    else:
        request["max_completion_tokens"] = 1200
    endpoint = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=request, timeout=90)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        data = _parse_json(content)
    except json.JSONDecodeError:
        retry_request = dict(request)
        retry_request["messages"] = [{"role": "user", "content": f"أعد كتابة النتيجة كـ JSON صحيح في سطر واحد فقط، بالمفتاحين title وcaption فقط. لا تستخدم Markdown ولا أسوار كود. الموضوع: {prompt}\nالمصادر:\n{sources}"}]
        retry = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=retry_request, timeout=90)
        retry.raise_for_status()
        retry_content = retry.json()["choices"][0]["message"]["content"]
        try:
            data = _parse_json(retry_content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini returned invalid JSON after retry: {retry_content[:300]}") from exc
    for key in ("title", "caption"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"AI response missing {key}")
    return data
