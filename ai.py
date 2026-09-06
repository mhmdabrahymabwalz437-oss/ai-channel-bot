import json
from openai import OpenAI

SYSTEM = """أنت محرر محتوى عربي محترف. أنشئ منشورا أصليا مفيدا اعتمادا على البرومبت والمصادر. لا تنسخ النصوص. اذكر المصدر في آخر الكابشن. أخرج JSON فقط."""


def generate(prompt: str, items, api_key: str, base_url: str, model: str) -> dict:
    client = OpenAI(api_key=api_key, base_url=base_url)
    sources = "\n".join(f"- {x.title}: {x.summary[:500]} ({x.url})" for x in items)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"البرومبت: {prompt}\nالمصادر:\n{sources}"}],
        response_format={"type": "json_object"},
        max_completion_tokens=1200,
    )
    data = json.loads(response.choices[0].message.content)
    for key in ("title", "caption"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"AI response missing {key}")
    return data
