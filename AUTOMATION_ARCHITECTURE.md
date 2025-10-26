# Browser Automation Architecture Documentation

## 🏗️ Общая Архитектура

### Компоненты Системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ AutomationPage │  │ Planner.ts   │  │ Validator.ts │        │
│  │   (UI Layer)   │→ │  (Planning)  │→ │ (Validation) │        │
│  └────────────────┘  └──────────────┘  └──────────────┘        │
│           ↓                                                      │
│  ┌────────────────────────────────────────────────────┐        │
│  │         ExecutionAgent.ts (Orchestrator)           │        │
│  │  - Управление workflow                              │        │
│  │  - State management                                 │        │
│  │  - Retry logic                                      │        │
│  └────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTP API
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │        automation_routes.py (REST API)              │        │
│  └─────────────────────────────────────────────────────┘        │
│           ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐        │
│  │    browser_automation_service.py (Core Logic)       │        │
│  │  - Session management                                │        │
│  │  - Playwright integration                            │        │
│  │  - Screenshot capture                                │        │
│  │  - Element interaction                               │        │
│  └─────────────────────────────────────────────────────┘        │
│           ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐        │
│  │      local_vision_service.py (AI Vision)            │        │
│  │  - Local Hugging Face model                          │        │
│  │  - Element detection on screenshots                  │        │
│  │  - Bounding box extraction                           │        │
│  │  - Text recognition (OCR)                            │        │
│  └─────────────────────────────────────────────────────┘        │
│           ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐        │
│  │           Playwright (Real Browser)                  │        │
│  │  - Chromium headless                                 │        │
│  │  - Page navigation                                   │        │
│  │  - DOM manipulation                                  │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Workflow Execution Pipeline

### Phase 1: Planning (Frontend)

**Файл:** `/app/frontend/src/agent/planner.ts`

**Функция:** `getPlan(goal: string) → PlannerResponse`

**Логика:**
1. Анализирует цель пользователя
2. Опционально использует Research Planner для сложных задач
3. Применяет **pattern matching** для определения типа задачи:
   - Gmail registration
   - E-commerce shopping
   - Login flows
   - Search operations
   - Form filling
   - Generic tasks

**Выход:** `ActionPlan` - массив `ActionStep[]`

```typescript
interface ActionStep {
  id: string;
  actionType: 'NAVIGATE' | 'CLICK' | 'TYPE' | 'WAIT' | 'SCROLL' | 'CAPTCHA';
  targetDescription: string;    // Human-readable description
  targetSelector?: string;       // CSS selector (if known)
  inputValue?: string;           // For TYPE actions
  expectedOutcome: string;       // What should happen
  retryCount?: number;
  maxRetries?: number;           // Default: 3
}
```

**Пример плана для Gmail:**
```javascript
[
  { actionType: 'NAVIGATE', targetDescription: 'Google Account Creation Page' },
  { actionType: 'TYPE', targetDescription: 'First Name field', targetSelector: 'input[name="firstName"]' },
  { actionType: 'CLICK', targetDescription: 'Next button', targetSelector: 'button[type="button"]' },
  // ...
]
```

---

### Phase 2: Execution (Frontend → Backend)

**Файл:** `/app/frontend/src/agent/executionAgent.ts`

**Главная функция:** `startAutomation(goal, initialState)`

**Логика выполнения:**

```
1. CREATE_SESSION → Backend создает browser session
   ↓
2. GET_PLAN → Planner возвращает ActionPlan
   ↓
3. FOR каждый step IN plan:
   ├─ executeStepWithRetry(step)
   │  ├─ performStep(step) → API call к backend
   │  ├─ Validator.check(result) → проверка успешности
   │  └─ IF fail AND retries < max → RETRY
   ├─ UPDATE browserState (screenshot, URL, highlight boxes)
   └─ ADD log entry
   ↓
4. FINAL_VALIDATION → проверка итогового результата
   ↓
5. CLEANUP_SESSION → закрытие браузера
```

**Retry Logic:**
- Каждый шаг имеет `maxRetries` (по умолчанию 3)
- При fail вызывается Validator для анализа
- Validator возвращает `shouldRetry: boolean`
- Если `shouldRetry && attempt < maxRetries` → повтор
- Иначе → fail всей автоматизации

**State Updates:**
Все изменения передаются через callback:
```typescript
executionAgent.setStateCallback((updates) => {
  // Updates включают:
  // - browserState (screenshot, URL, highlightBoxes)
  // - logEntries (новые записи)
  // - status ('planning' | 'executing' | 'completed' | 'failed')
  // - currentStepIndex
});
```

---

### Phase 3: Browser Interaction (Backend)

**Файл:** `/app/backend/services/browser_automation_service.py`

**Класс:** `BrowserAutomationService`

#### Session Management

```python
async def create_session(session_id: str):
    # 1. Initialize Playwright if not done
    # 2. Launch headless Chromium with options:
    #    - --no-sandbox
    #    - --disable-setuid-sandbox
    #    - --disable-blink-features=AutomationControlled (anti-detection)
    # 3. Create new BrowserContext with:
    #    - viewport: 1280x720
    #    - user_agent: realistic UA string
    # 4. Create new Page
    # 5. Store in sessions dict: {session_id: {context, page, history}}
```

#### Core Actions

**Navigate:**
```python
async def navigate(session_id, url):
    # 1. Get page from session
    # 2. page.goto(url, wait_until='networkidle', timeout=30s)
    # 3. Capture screenshot
    # 4. Get title and current URL
    # 5. Return {success, url, title, screenshot}
```

**Click Element:**
```python
async def click_element(session_id, selector):
    # 1. Wait for selector (timeout: 10s)
    # 2. Get element bounding box для highlight
    # 3. page.click(selector)
    # 4. Wait 1s для завершения action
    # 5. Capture screenshot
    # 6. Return {success, screenshot, highlight: {x, y, w, h}}
```

**Type Text:**
```python
async def type_text(session_id, selector, text):
    # 1. Wait for selector
    # 2. Get element bounding box
    # 3. page.fill(selector, text)
    # 4. Wait 500ms
    # 5. Capture screenshot
    # 6. Return {success, screenshot, highlight}
```

**Screenshot Capture:**
```python
async def capture_screenshot(session_id):
    # 1. page.screenshot(type='png', full_page=False)
    # 2. Base64 encode
    # 3. Return f"data:image/png;base64,{screenshot_base64}"
```

#### Element Finding (с Vision Model)

```python
async def find_elements_with_vision(session_id, description):
    # 1. Capture screenshot
    # 2. Call local_vision_service.find_element(screenshot, description)
    # 3. Vision model возвращает:
    #    - Bounding boxes элементов
    #    - Confidence scores
    #    - Text labels (OCR)
    # 4. Map bounding boxes to CSS selectors (approximate)
    # 5. Return [{selector, text, box, confidence}]
```

---

### Phase 4: Validation (Frontend)

**Файл:** `/app/frontend/src/agent/validator.ts`

**Класс:** `ValidatorService`

**Функция:** `check(browserState, step, attempt) → ValidatorResponse`

**Логика проверки:**

```javascript
switch (step.actionType) {
  case 'NAVIGATE':
    // Проверить: URL changed, page loaded (has screenshot)
    // Success rate: 85%
    
  case 'CLICK':
    // Проверить: page changed, timestamp fresh
    // Success rate: 80%
    
  case 'TYPE':
    // Проверить: input accepted, no errors
    // Success rate: 90%
    
  case 'SUBMIT':
    // Проверить: form submitted, no validation errors
    // Success rate: 75%
    
  case 'CAPTCHA':
    // Проверить: CAPTCHA solved
    // Success rate: 60% (lowest)
}
```

**ValidatorResponse:**
```typescript
{
  isValid: boolean,           // Pass or fail
  confidence: number,         // 0.0 - 1.0
  issues: string[],          // List of problems
  shouldRetry: boolean,      // Recommend retry?
  suggestions?: string[]     // How to fix
}
```

**Final Validation:**
После всех шагов вызывается `validateFinalResult(browserState, goal)` для проверки достижения цели.

---

## 🔧 Расширяемость

### Добавление нового ActionType

1. **Обновить types.ts:**
```typescript
export type ActionType = 
  | 'NAVIGATE' | 'CLICK' | 'TYPE' | 'WAIT' 
  | 'NEW_ACTION';  // ← Добавить здесь
```

2. **Обновить Planner:**
```typescript
// В generateStepsForGoal() добавить логику
if (goalLower.includes('new_action')) {
  return this.generateNewActionSteps();
}
```

3. **Обновить ExecutionAgent (performStep):**
```typescript
case 'NEW_ACTION':
  response = await fetch(`${API}/automation/new-action`, {
    method: 'POST',
    body: JSON.stringify({ session_id, ...params })
  });
  break;
```

4. **Добавить Backend endpoint:**
```python
@router.post("/new-action")
async def new_action(request: NewActionRequest):
    result = await browser_service.perform_new_action(...)
    return result
```

5. **Обновить Validator:**
```typescript
case 'NEW_ACTION':
  return this.validateNewAction(browserState, step);
```

### Добавление нового Pattern в Planner

```typescript
// В planner.ts
private generateNewPatternSteps(goal: string): ActionStep[] {
  return [
    {
      id: 'step-1',
      actionType: 'NAVIGATE',
      targetDescription: 'Target page',
      expectedOutcome: 'Page loads',
      maxRetries: 3
    },
    // ... остальные шаги
  ];
}

// В generateStepsForGoal()
if (goalLower.includes('new_pattern_keyword')) {
  return this.generateNewPatternSteps(goal);
}
```

---

## 🎯 Использование Local Vision Model

### Integration Points

**1. Element Detection (вместо CSS selectors):**
```python
# Вместо hardcoded селектора:
selector = 'input[name="email"]'

# Vision model находит элемент:
elements = await vision_service.find_element(
    screenshot=screenshot,
    description="email input field"
)
# Returns: [{box: {x, y, w, h}, confidence: 0.95}]
```

**2. Verification после actions:**
```python
# После клика проверить что элемент изменился:
before_screenshot = capture_screenshot()
await click_element(selector)
after_screenshot = capture_screenshot()

changes = vision_service.compare_screenshots(before, after)
# Returns: [{region: {x,y,w,h}, change_type: 'color'|'text'|'visibility'}]
```

**3. Form field recognition:**
```python
# Автоматическое заполнение форм:
form_fields = vision_service.detect_form_fields(screenshot)
# Returns: [
#   {type: 'email', label: 'Email', box: {...}},
#   {type: 'password', label: 'Password', box: {...}}
# ]
```

---

## 📊 Data Flow

### Session Creation → Execution → Cleanup

```
USER INPUT: "Register Gmail account"
    ↓
PLANNER: Generate 7-step plan
    ↓
EXECUTION AGENT:
  ├─ Create browser session (Playwright)
  ├─ Step 1: NAVIGATE to google.com/signup
  │   ├─ Backend: page.goto()
  │   ├─ Screenshot captured
  │   └─ Validator: ✓ Page loaded
  ├─ Step 2: TYPE first name
  │   ├─ Vision model: Find "First Name" field → box {x,y,w,h}
  │   ├─ Backend: page.click(x, y) → page.type(text)
  │   ├─ Screenshot captured
  │   └─ Validator: ✓ Text entered
  ├─ Step 3: CLICK Next button
  │   ├─ Vision model: Find "Next" button
  │   ├─ Backend: page.click()
  │   ├─ Screenshot captured
  │   └─ Validator: ✓ Page changed
  └─ ... (remaining steps)
    ↓
FINAL VALIDATION: Check success criteria
    ↓
CLEANUP: Close browser session
    ↓
RESULT: {success: true, payload: {email, password}, screenshot}
```

---

## 🚀 Performance & Optimization

### Screenshot Optimization
- **Format:** PNG (base64)
- **Size:** ~50-200KB per screenshot
- **Compression:** Quality reduced for faster transfer
- **Caching:** Vision model results cached per screenshot hash

### Vision Model Optimization
- **Model:** Local on-device (no API calls)
- **Inference time:** ~100-500ms per screenshot
- **Batch processing:** Multiple elements detected in single pass
- **Memory:** Model loaded once, kept in RAM

### Session Management
- **Max concurrent sessions:** 5 (configurable)
- **Idle timeout:** 5 minutes
- **Auto-cleanup:** On completion or error
- **Resource limits:** CPU/memory monitored

---

## 🔐 Security Considerations

### Anti-Detection
- User-Agent rotation
- `--disable-blink-features=AutomationControlled` flag
- Random delays between actions (humanization)
- Viewport size randomization

### Data Privacy
- Screenshots stored temporarily in memory only
- No persistent storage of sensitive data
- Sessions isolated (separate BrowserContext per user)
- Credentials never logged

---

## 🐛 Error Handling

### Типы ошибок:

1. **Navigation Errors:**
   - Timeout → Retry with longer timeout
   - 404/500 → Fail immediately
   - SSL errors → Retry once

2. **Element Not Found:**
   - CSS selector failed → Use vision model
   - Vision model failed → Try different description
   - Still not found → Skip step or fail

3. **Action Failures:**
   - Click intercepted → Wait for modal/overlay to close
   - Type blocked → Check field is editable
   - Submit failed → Check validation errors

4. **Browser Crashes:**
   - Restart browser
   - Resume from last successful step
   - Notify user

### Logging

```python
logger.info(f"[Session {session_id}] Action: {action_type}")
logger.debug(f"Screenshot size: {len(screenshot)} bytes")
logger.error(f"Failed to find element: {selector}", exc_info=True)
```

---

## 📈 Future Enhancements

1. **Multi-tab support** - управление несколькими вкладками
2. **File downloads** - обработка скачиваний
3. **Cookie management** - сохранение/восстановление cookies
4. **Proxy support** - routing через прокси
5. **CAPTCHA solving** - интеграция с решателями капчи
6. **Scheduled tasks** - запланированные автоматизации
7. **Parallel execution** - одновременное выполнение задач
8. **Visual regression testing** - сравнение UI versions

---

**Версия документации:** 1.0  
**Дата:** 2025-10-26  
**Автор:** AI Development Team
