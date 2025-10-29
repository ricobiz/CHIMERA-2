# Chimera AIOS - Brain Architecture (3-Level Model System)

## Обзор

Система автоматизации браузера использует **3-уровневую архитектуру** для оптимизации стоимости и производительности:

```
┌─────────────────────────────────────────────────────────────┐
│                     ГОЛОВНОЙ МОЗГ                            │
│              (Head Brain - Главная модель)                   │
│                                                               │
│  Модель: GPT-5 / Claude Sonnet 4 / Grok 4 / Gemini Pro     │
│  Назначение: Анализ задачи + Стратегия + Генерация данных   │
│  Частота вызова: ОДИН РАЗ в начале                          │
│  Стоимость: Высокая                                          │
└─────────────────────────────────────────────────────────────┘
                             ↓
                    Передаёт ПЛАН + ДАННЫЕ
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     СПИННОЙ МОЗГ                             │
│              (Spinal Cord - Средняя модель)                  │
│                                                               │
│  Модель: Qwen 2.5 VL / Google 2.5 Vision / Gemini Flash    │
│  Назначение: Принятие решений в реальном времени            │
│  Частота вызова: ЦИКЛИЧЕСКИ (каждый шаг)                    │
│  Стоимость: Средняя/Низкая                                   │
└─────────────────────────────────────────────────────────────┘
                             ↓
                    Даёт команды ИСПОЛНИТЕЛЮ
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     ИСПОЛНИТЕЛЬ                              │
│           (Executor - Маленькая локальная модель)            │
│                                                               │
│  Модель: Florence-2 ONNX / Mini Selector / DOM fallback    │
│  Назначение: Видеть экран + Выполнять клики                 │
│  Частота вызова: ПОСТОЯННО                                   │
│  Стоимость: БЕСПЛАТНО (локально)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Детальное описание уровней

### 1. Головной мозг (Head Brain)

**Файл:** `/app/backend/services/head_brain_service.py`

**Ответственность:**
- Анализ задачи пользователя (например: "Зарегистрировать Gmail аккаунт")
- Определение требований:
  - Нужен ли прогретый профиль?
  - Нужен ли телефон?
  - Какие данные необходимы? (имя, фамилия, пароль)
- Создание стратегии выполнения
- Генерация необходимых данных (имя, email, пароль, дата рождения)
- Оценка вероятности успеха

**Когда вызывается:**
- ОДИН РАЗ в самом начале при вызове `/api/hook/exec`

**Выход:**
```json
{
  "task_id": "head-1234",
  "understood_task": "Register Gmail account without phone",
  "requirements": {
    "needs_warm_profile": true,
    "needs_phone": false,
    "mandatory_data": ["first_name", "last_name", "username", "password", "birthday"]
  },
  "strategy": "attempt_without_phone",
  "success_probability": 0.65,
  "plan_outline": "Navigate → Fill registration form → Handle captcha → Submit",
  "data_bundle": {
    "first_name": "Ivan",
    "last_name": "Petrov",
    "username": "ivan.petrov.1234",
    "password": "Abc123!@#",
    "birthday": "1995-06-15"
  },
  "can_proceed": true
}
```

**Модели (назначаемые):**
- `openai/gpt-5` (по умолчанию)
- `anthropic/claude-3.5-sonnet`
- `x-ai/grok-4`
- `google/gemini-2.5-flash`

---

### 2. Спинной мозг (Spinal Cord / Brain)

**Файл:** `/app/backend/services/supervisor_service.py`

**Ответственность:**
- Получение плана от головного мозга
- Анализ текущего состояния экрана (screenshot + vision)
- Сопоставление реальности с планом
- Принятие решения о следующем действии:
  - `CLICK_CELL` - кликнуть по ячейке grid
  - `TYPE_AT_CELL` - ввести текст в ячейку
  - `SCROLL` - прокрутить страницу
  - `WAIT` - подождать
  - `DONE` - задача выполнена
  - `ERROR` - проблема, нужна помощь

**Когда вызывается:**
- ЦИКЛИЧЕСКИ в процессе выполнения (каждый шаг)
- До 50 итераций на одну задачу

**Вход:**
```json
{
  "goal": "Register Gmail | Strategy: attempt_without_phone | Data: [first_name, last_name, ...]",
  "history": [{"step": 1, "action": "NAVIGATE", ...}],
  "screenshot_base64": "iVBORw0KGgo...",
  "vision": [
    {"cell": "C5", "label": "Email field", "type": "input", "confidence": 0.92},
    {"cell": "D8", "label": "Next button", "type": "button", "confidence": 0.95}
  ]
}
```

**Выход:**
```json
{
  "next_action": "TYPE_AT_CELL",
  "target_cell": "C5",
  "text": "ivan.petrov.1234",
  "confidence": 0.85
}
```

**Модели (дешёвые vision):**
- `qwen/qwen2.5-vl` (по умолчанию)
- `google/gemini-2.0-flash-thinking-exp:free`

---

### 3. Исполнитель (Executor)

**Файл:** `/app/backend/services/local_vision_service.py`

**Ответственность:**
- Видеть экран в реальном времени
- Распознавать элементы UI (кнопки, поля ввода)
- Выполнять базовые действия:
  - Клики
  - Ввод текста
  - Скроллинг
- Проверять изменения после действия
- При затруднениях → передавать спинному мозгу

**Когда вызывается:**
- ПОСТОЯННО в фоновом режиме
- При каждом запросе screenshot/vision

**Технологии:**
- ONNX модель (Florence-2) - если доступна
- Fallback на DOM-анализ
- Grid-based координаты (A1, B5, C7 и т.д.)

**Преимущества:**
- Полностью бесплатно (локально)
- Быстрая реакция
- Не требует API ключей

---

## Поток выполнения

### Пример: Регистрация Gmail аккаунта

```
1. Пользователь → "Register a new Gmail account"
   ↓
2. ГОЛОВНОЙ МОЗГ (один раз):
   ✓ Анализ: "Нужна регистрация на строгом сайте"
   ✓ Проверка: Прогретый профиль ДОСТУПЕН
   ✓ Стратегия: "attempt_without_phone"
   ✓ Генерация данных: Ivan Petrov, ivan.petrov.4523@gmail.com, Abc789!@#
   ✓ План: "Navigate → Fill → Captcha → Submit"
   ↓
3. Создание сессии с прогретым профилем
   ↓
4. ЦИКЛ (СПИННОЙ МОЗГ + ИСПОЛНИТЕЛЬ):
   
   Шаг 1:
   - ИСПОЛНИТЕЛЬ: Скриншот + Vision элементы
   - СПИННОЙ МОЗГ: "NAVIGATE to https://accounts.google.com/signup"
   - ИСПОЛНИТЕЛЬ: Переход на страницу
   
   Шаг 2:
   - ИСПОЛНИТЕЛЬ: Скриншот новой страницы
   - СПИННОЙ МОЗГ: "TYPE_AT_CELL C5 'Ivan'" (поле First Name)
   - ИСПОЛНИТЕЛЬ: Ввод текста
   
   Шаг 3:
   - ИСПОЛНИТЕЛЬ: Скриншот
   - СПИННОЙ МОЗГ: "TYPE_AT_CELL D5 'Petrov'" (поле Last Name)
   - ИСПОЛНИТЕЛЬ: Ввод текста
   
   ... и так далее до завершения
   
   Шаг N:
   - СПИННОЙ МОЗГ: "DONE"
   - Цикл завершён
```

---

## Ключевые преимущества архитектуры

### 1. Экономия токенов
- Дорогая модель (GPT-5) вызывается **ОДИН РАЗ**
- Дешёвая модель (Qwen VL) работает циклически
- Локальная модель (Florence-2) **БЕСПЛАТНА**

### 2. Адаптивность
- План не статичен - адаптируется к реальности
- Спинной мозг видит изменения и реагирует
- Может справиться с неожиданностями (капча, новые поля)

### 3. Прогретые профили
- **Критично** для регистрации без телефона
- Профиль имитирует реального пользователя:
  - История браузера
  - Cookies
  - Canvas fingerprint
  - WebGL fingerprint
  - Residential прокси
  - Human-like поведение

### 4. Анти-бот защита
- Профили с warmup (прогревом)
- Human Behavior Simulator:
  - Bezier кривые для мыши
  - Случайные паузы
  - Опечатки при вводе
  - Естественная скорость

---

## API Endpoints

### `/api/hook/exec` - Главная точка входа

**POST** `/api/hook/exec`

**Request:**
```json
{
  "text": "Register a new Gmail account",
  "timestamp": 1761701234567,
  "nocache": true
}
```

**Response (Success):**
```json
{
  "status": "ACTIVE",
  "job_id": "abc-123-def",
  "session_id": "session-456",
  "steps_executed": 15,
  "head_analysis": {
    "task_id": "head-789",
    "analysis": {
      "understood_task": "Register Gmail account",
      "requirements": {...},
      "decision": {
        "can_proceed": true,
        "strategy": "attempt_without_phone",
        "success_probability": 0.65
      }
    }
  }
}
```

**Response (Needs Requirements):**
```json
{
  "status": "NEEDS_REQUIREMENTS",
  "job_id": "abc-123-def",
  "analysis": {...},
  "message": "Need warm profile or phone number"
}
```

---

## Конфигурация

### Переменные окружения

```bash
# Головной мозг
HEAD_BRAIN_MODEL=openai/gpt-4o

# Спинной мозг (используется в supervisor_service)
AUTOMATION_VLM_MODEL=qwen/qwen2.5-vl

# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_HTTP_REFERER=https://chimera-aios.app
OPENROUTER_X_TITLE=Chimera AIOS

# Профили
PROFILES_DIR=/app/backend/profiles
```

---

## Troubleshooting

### Проблема: "NEEDS_REQUIREMENTS" - Need warm profile

**Причина:** Нет прогретого профиля для строгого сайта

**Решение:**
```bash
curl -X POST http://localhost:8001/api/profile/create \
  -H "Content-Type: application/json" \
  -d '{"warmup": true, "region": "US"}'
```

### Проблема: Головной мозг не работает

**Причина:** Не установлен OPENROUTER_API_KEY или модель недоступна

**Решение:**
1. Проверьте ключ: `echo $OPENROUTER_API_KEY`
2. Смените модель: `HEAD_BRAIN_MODEL=anthropic/claude-3.5-sonnet`
3. Проверьте логи: `tail -f /var/log/supervisor/backend.out.log | grep "HEAD BRAIN"`

### Проблема: Спинной мозг делает странные действия

**Причина:** Недостаточно контекста или плохое качество vision

**Решение:**
1. Увеличьте grid density для более точных координат
2. Убедитесь что vision модель видит все элементы
3. Добавьте больше примеров в промпт supervisor_service

---

## Следующие шаги для разработки

1. **Интеграция с фронтендом:**
   - Отображение strategy от головного мозга
   - Показ data_bundle в UI
   - Индикатор "warm profile needed"

2. **Улучшение головного мозга:**
   - Более сложные стратегии
   - Поддержка multi-step планов
   - Адаптация на основе feedback

3. **Расширение спинного мозга:**
   - Поддержка более сложных действий
   - Лучшее распознавание капчи
   - Более умное восстановление после ошибок

4. **Оптимизация исполнителя:**
   - Подключение реальной ONNX модели
   - Улучшение DOM fallback
   - Кэширование vision результатов

---

## Авторы

- Chimera AIOS Team
- Документация обновлена: 2025-01-28
