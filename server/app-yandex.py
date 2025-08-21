from flask import Flask, request, jsonify, send_from_directory
import subprocess, requests, datetime as dt

app = Flask(__name__, static_url_path='/static')

# твоё окружение
FOLDER_ID = "b1gc0e0lvqserhatgfg9"
YC_BIN = "/Users/sergeyluzhin/yandex-cloud/bin/yc"  # абсолютный путь к yc

# ---------- базовые функции ----------
def get_iam_token():
    """Получает IAM-токен через yc CLI."""
    result = subprocess.run([YC_BIN, "iam", "create-token"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yc error: {result.stderr.strip()}")
    return result.stdout.strip()

def call_yandex_gpt(prompt, *, max_tokens=700, temperature=0.6):
    """Вызывает YandexGPT с произвольным промптом и возвращает текст."""
    token = get_iam_token()
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": temperature, "maxTokens": max_tokens},
        "messages": [{"role": "user", "text": prompt}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["result"]["alternatives"][0]["message"]["text"]

# ---------- старый endpoint: краткое описание города ----------
def get_city_description(city_name: str) -> str:
    prompt = f"Напиши краткое описание города {city_name}. Максимум 3–4 предложения."
    try:
        return call_yandex_gpt(prompt, max_tokens=220, temperature=0.6)
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/describe', methods=['POST'])
def describe():
    data = request.get_json(force=True) or {}
    city = (data.get("city") or "").strip()
    if not city:
        return jsonify({"error": "Не указано название города"}), 400
    return jsonify({"description": get_city_description(city)})

# ---------- новый endpoint: генерация тура по всем полям ----------
@app.route('/generate-tour', methods=['POST'])
def generate_tour():
    data = request.get_json(force=True) or {}

    city = (data.get("city") or "").strip()
    budget = data.get("budget")
    start = (data.get("startDate") or "").strip()     # yyyy-mm-dd из <input type="date">
    end = (data.get("endDate") or "").strip()
    people = data.get("people")
    activities = data.get("activities") or []         # массив строк (подписи чекбоксов)

    # валидация
    if not (city and budget is not None and start and end and people):
        return jsonify({"error": "Заполните город, бюджет, даты и количество туристов."}), 400

    # длительность, если даты валидные
    days_phrase = f"Даты: {start} — {end}."
    try:
        sd, ed = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
        days = (ed - sd).days + 1
        if days > 0:
            days_phrase = f"Длительность: {days} дней ({start} — {end})."
    except Exception:
        pass

    activities_str = ", ".join(activities) if activities else "без выраженных предпочтений"

    prompt = (
        f"Составь персональный план путешествия в город {city} для {people} человек. "
        f"Бюджет всей поездки: {budget} ₽. {days_phrase} "
        f"Предпочтения по активностям: {activities_str}. "
        "Сделай структурированный план по дням (утро/день/вечер), указывай ориентировочные цены, "
        "предлагай недорогие альтернативы, локальные советы по транспорту и еде. Ответ на русском, лаконично."
    )

    try:
        plan = call_yandex_gpt(prompt, max_tokens=900, temperature=0.7)
        return jsonify({"plan": plan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- статика / страница ----------
@app.route('/')
def serve_index():
    return send_from_directory('sindbad', 'generate-a-tour.html')


if __name__ == '__main__':
    app.run(debug=True)
