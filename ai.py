import json
import requests

SYSTEM = """أنت محرر محتوى عربي محترف. أنشئ منشورا أصليا مفيدا اعتمادا على البرومبت والمصادر. لا تنسخ النصوص. اذكر المصدر في آخر الكابشن. أخرج JSON فقط."""


def generate(prompt: str, items, api_key: str, base_url: str, model: str) -> dict:
    sources = "\n".join(f"- {x.title}: {x.summary[:500]} ({x.url})" for x in items)
    request = dict(
        model=model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"البرومبت: {prompt}\nالمصادر:\n{sources}"}],
        response_format={"type": "json_object"},
    )
    if "generativelanguage.googleapis.com" in base_url:
        request["max_tokens"] = 1200
    else:
        request["max_completion_tokens"] = 1200
    endpoint = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=request, timeout=90)
    response.raise_for_status()
    data = json.loads(response.json()["choices"][0]["message"]["content"])
    for key in ("title", "caption"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"AI response missing {key}")
    return data
