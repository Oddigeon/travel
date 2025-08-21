// static/script.js
document.addEventListener('DOMContentLoaded', () => {
  // Контейнер для вывода результата
  let out = document.getElementById('description');
  if (!out) {
    out = document.createElement('div');
    out.id = 'description';
    out.className = 'col-md-8 mx-auto mt-4';
    document.body.appendChild(out);
  }

  // Элементы формы
  const form = document.getElementById('tourForm'); // может отсутствовать
  const submitBtn = document.querySelector('button[type="submit"]');

  const el = {
    city: document.getElementById('cityInput'),
    budget: document.getElementById('budgetInput'),
    start: document.getElementById('startDate'),
    end: document.getElementById('endDate'),
    people: document.getElementById('peopleCount'),
  };

  // общая функция валидации
  function validate() {
    let ok = true;

    const mark = (input, condition) => {
      if (!input) return;
      if (!condition) {
        input.classList.add('is-invalid');
        ok = false;
      } else {
        input.classList.remove('is-invalid');
      }
    };

    const budgetNum = Number(el.budget?.value);
    const peopleNum = Number(el.people?.value);

    mark(el.city, Boolean(el.city?.value.trim()));
    mark(el.budget, Number.isFinite(budgetNum) && budgetNum > 0);
    mark(el.start, Boolean(el.start?.value));
    mark(el.end, Boolean(el.end?.value));
    mark(el.people, Number.isInteger(peopleNum) && peopleNum >= 1);

    // проверка порядка дат
    if (el.start?.value && el.end?.value) {
      const sd = new Date(el.start.value);
      const ed = new Date(el.end.value);
      if (ed < sd) {
        el.end.classList.add('is-invalid');
        ok = false;
      }
    }

    // проскроллить к первому невалидному
    if (!ok) {
      const firstInvalid = document.querySelector('.is-invalid');
      firstInvalid?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return ok;
  }

  // сбор данных
  function collectPayload() {
    const city = el.city?.value.trim() || '';
    const budget = Number(el.budget?.value || 0);
    const startDate = el.start?.value || '';   // yyyy-mm-dd
    const endDate = el.end?.value || '';
    const people = Number(el.people?.value || 0);

    const activities = Array.from(document.querySelectorAll('input[name="activities"]:checked'))
      .map((input) => {
        const lbl = document.querySelector(`label[for="${input.id}"]`);
        return (lbl?.textContent || input.value || input.id).trim();
      });

    return { city, budget, startDate, endDate, people, activities };
  }

  async function submitHandler(e) {
    if (e) e.preventDefault();
    out.textContent = '';

    if (!validate()) return;

    const payload = collectPayload();
    out.textContent = 'Генерируем тур...';

    try {
      const res = await fetch('/generate-tour', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }

      const data = await res.json();
      const text = data.plan || data.description || 'Нет данных.';
      out.innerHTML = String(text).replaceAll('\n', '<br>');
    } catch (err) {
      console.error(err);
      out.textContent = 'Ошибка при получении ответа от сервера.';
    }
  }

  // Привязки: либо submit формы, либо клик по кнопке
  if (form) {
    form.addEventListener('submit', submitHandler);
  }
  if (submitBtn) {
    submitBtn.addEventListener('click', submitHandler);
  }
});
