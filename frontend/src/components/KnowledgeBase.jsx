import React, { useState } from 'react';
import { Book, ChevronDown, ChevronRight, X } from 'lucide-react';

const KnowledgeBase = ({ onClose, language = 'en' }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  const knowledgeBase = {
    en: {
      title: "CHIMERA AIOS - Complete Guide",
      subtitle: "Advanced AI Operating System for Automation & Development",
      sections: [
        {
          id: 'overview',
          title: '📋 Platform Overview',
          content: `CHIMERA AIOS is an advanced AI-powered operating system that combines multiple cutting-edge AI models to provide comprehensive automation, development, and analysis capabilities.

**Key Features:**
- Multi-model AI architecture (GPT-5, Claude 4.5, Gemini, Grok)
- Natural language task routing
- Real-time code generation and preview
- Browser automation with AI vision
- Document verification system
- Self-optimization capabilities`
        },
        {
          id: 'code-generation',
          title: '⚡ AI Code Generation',
          content: `**How to use:**
1. Simply describe your app idea in natural language
2. Chimera automatically generates full-stack code (React + FastAPI + MongoDB)
3. View live preview instantly
4. Export or modify as needed

**Models used:**
- Primary: Grok Beta (fast, optimized for code)
- Planning: GPT-5 + Claude 3.5 Sonnet

**Features:**
- Real-time code preview
- Automatic dependency management
- MongoDB integration
- Export to GitHub or download ZIP
- Session persistence

**Example prompts:**
- "Build a todo app with drag-and-drop"
- "Create a dashboard with charts and graphs"
- "Make a chat application with real-time messaging"`
        },
        {
          id: 'design-first',
          title: '🎨 Design-First Workflow',
          content: `**How it works:**
1. Describe your app's visual design
2. AI generates detailed design specification
3. Visual validator checks the design
4. You approve or revise
5. Code is generated matching the design

**Models used:**
- Design Generation: Gemini 2.5 Nano Banana ($0.01/1M tokens)
- Visual Validation: Gemini 2.5 Nano Banana

**Benefits:**
- Ensures UI matches requirements before coding
- Cost-effective vision model
- Reduces iterations
- Professional design output

**Example:**
"Design a modern dark theme dashboard with sidebar navigation, statistics cards, and a data table"`
        },
        {
          id: 'browser-automation',
          title: '🤖 Browser Automation',
          content: `**How to use:**
Simply describe what you want to automate in natural language. The system automatically detects it's an automation task.

**Examples:**
- "Go to Google and search for AI"
- "Navigate to Twitter and login"
- "Fill out this registration form"
- "Click the buy button and checkout"

**How it works:**
1. AI classifies your message as automation task
2. Planning agent creates step-by-step plan
3. Browser opens and executes steps
4. Local vision model finds elements (FREE)
5. Validates each action
6. Returns results

**Models used:**
- Planning: GPT-5 (complex task decomposition)
- Vision: Local Model (FREE, fast element detection)
- Validation: Nano Banana

**Features:**
- Natural language commands
- No selectors needed
- Screenshot validation
- Pause/resume control
- Detailed logging

**Advanced:**
- Smart click: Finds elements by description
- Smart type: Fills forms intelligently
- Wait conditions: Adapts to page loading
- Error recovery: Retries on failure`
        },
        {
          id: 'document-verification',
          title: '📄 Document Verification',
          content: `**How to use:**
1. Upload document image
2. System analyzes with 3 top AI models
3. Get consensus verdict with confidence score

**Models used (Triple Verification):**
1. GPT-5: Deep content analysis
2. Claude 4.5 Sonnet: Structural verification
3. Gemini 2.5 Flash Vision: Visual authenticity

**What it detects:**
- AI-generated content
- Document forgery
- Photoshop manipulation
- Inconsistent metadata
- Tampered signatures
- Fake watermarks

**Output:**
- Fraud probability (0-100%)
- Red flags list
- Authenticity indicators
- Model agreement level
- Detailed analysis from each model

**Use cases:**
- ID verification
- Contract validation
- Certificate authentication
- Invoice fraud detection
- Legal document verification`
        },
        {
          id: 'self-improvement',
          title: '🧠 Self-Improvement System',
          content: `**Features:**
1. **Model Optimization**
   - Automatically selects best models for each task
   - Balances cost vs quality
   - Uses FREE models where possible
   - Real-time cost tracking

2. **Code Analysis**
   - Reviews own codebase
   - Detects security issues
   - Finds performance bottlenecks
   - Suggests improvements

3. **Auto-Optimization**
   - Applies safe fixes automatically
   - Reloads services after changes
   - Tracks optimization history
   - Rollback capability

**Models used:**
- Analysis: Claude 3.5 Sonnet (excellent code understanding)
- Optimization: GPT-5 or Claude 4.5

**How to use:**
1. Click "Self-Improvement" in settings
2. View current model assignments
3. Click "Optimize Models" to auto-select best models
4. Review system health
5. Analyze code for improvements
6. Apply optimizations

**Model Assignments:**
- Code Gen: Grok Beta ($5/1M)
- Design: Nano Banana ($0.01/1M) 
- Automation Vision: Local Model (FREE)
- Planning: GPT-5 ($15/1M)
- Verification: Multi-model`
        },
        {
          id: 'context-management',
          title: '🔄 Context Management',
          content: `**Smart Context Handling:**
- Monitors token usage in real-time
- Automatically compresses when limit approached
- Creates new sessions with compressed context
- Transfers important information

**Features:**
- Dynamic context window tracking
- Model-specific limits (fetched from OpenRouter)
- Automatic session switching
- Context compression using AI
- Cost optimization

**Visual Indicators:**
- Green: Safe (<80% usage)
- Yellow: Warning (80-90%)
- Red: Critical (>90%)

**How it works:**
1. Tracks tokens for current model
2. Compresses old messages when needed
3. Creates new session if limit reached
4. Preserves key information
5. Seamless continuation

**Benefits:**
- Never lose conversation context
- Optimal token usage
- Cost savings
- No manual session management`
        },
        {
          id: 'session-management',
          title: '💾 Session Management',
          content: `**Features:**
- Automatic session creation
- Persistent storage in MongoDB
- Quick session switching
- Search and filter sessions
- Export session history

**Session includes:**
- All messages
- Generated code
- Design proposals
- Cost tracking
- Timestamps

**How to use:**
1. Click Chimera logo to view sessions
2. Select previous session to load
3. Continue from where you left off
4. Create new session anytime

**Benefits:**
- Never lose work
- Organize projects
- Review history
- Multi-project workflow`
        },
        {
          id: 'content-folder',
          title: '🗂️ Content Folder',
          content: `**What it stores:**
- Generated code files
- Design images
- Screenshots
- Documents
- Automation results

**Features:**
- Session-specific storage
- Organized by type
- Quick preview
- Download individual items
- Persist across sessions

**How to access:**
- Click folder icon (🗂️) in header
- View all session content
- Filter by type
- Download as needed

**Use cases:**
- Archive generated apps
- Save design iterations
- Export automation results
- Keep document analysis`
        },
        {
          id: 'personalization',
          title: '👤 Personalization',
          content: `**AI Assistant: Aria**
Your creative companion who:
- Speaks naturally (no "AI speak")
- Remembers your name
- Learns preferences
- Adapts communication style

**How it works:**
1. First time: Aria introduces herself
2. She asks your name
3. Name saved in local storage
4. Personalized greeting in all messages

**Benefits:**
- Human-like interaction
- Comfortable communication
- Relationship building
- Better collaboration

**Note:**
Aria never mentions she's an AI or model - she communicates like a talented colleague helping you build amazing things.`
        },
        {
          id: 'language',
          title: '🌐 Language Support',
          content: `**Supported Languages:**
- English (en)
- Русский (ru)

**How to switch:**
1. Open Settings (⚙️)
2. Select Language option
3. Choose preferred language
4. Interface updates instantly

**What's translated:**
- All UI elements
- Platform capabilities
- Knowledge Base
- Error messages
- Tooltips

**Note:**
AI responses adapt to your language automatically based on your messages.`
        },
        {
          id: 'cost-optimization',
          title: '💰 Cost Optimization',
          content: `**Strategy:**
- FREE models for simple tasks (local vision)
- Cheap models for design ($0.01/1M)
- Mid-range for code generation ($5/1M)
- Premium for complex planning ($15/1M)

**Current Costs:**
- Browser Vision: FREE (local model)
- Design/Validation: $0.01 per 1M tokens
- Code Generation: $5.00 per 1M tokens
- Planning: $15.00 per 1M tokens
- Triple Verification: Variable

**Savings Tips:**
1. Use automation vision (FREE)
2. Enable visual validator (cheap)
3. Let system optimize models
4. Monitor OpenRouter balance

**Real-time Tracking:**
- Cost per session
- Total platform cost
- Model-specific costs
- OpenRouter balance`
        },
        {
          id: 'tips-tricks',
          title: '💡 Tips & Best Practices',
          content: `**For Code Generation:**
- Be specific about functionality
- Mention tech stack if needed
- Describe UI/UX requirements
- Use iterative refinement

**For Browser Automation:**
- Use natural descriptions
- Be clear about goal
- Test with simple tasks first
- Review logs if issues

**For Document Verification:**
- Use high-quality images
- Include full document
- Wait for all 3 models
- Check agreement level

**General Tips:**
1. Start sessions for different projects
2. Use Content Folder to organize
3. Monitor context usage
4. Let Aria remember your name
5. Explore platform capabilities
6. Check Knowledge Base when stuck

**Keyboard Shortcuts:**
- Ctrl/Cmd + Enter: Send message
- Esc: Close modals
- Ctrl/Cmd + K: Search sessions`
        }
      ]
    },
    ru: {
      title: "CHIMERA AIOS - Полное Руководство",
      subtitle: "Продвинутая AI Операционная Система для Автоматизации и Разработки",
      sections: [
        {
          id: 'overview',
          title: '📋 Обзор Платформы',
          content: `CHIMERA AIOS — это продвинутая операционная система на базе AI, которая объединяет несколько передовых AI моделей для обеспечения комплексных возможностей автоматизации, разработки и анализа.

**Ключевые возможности:**
- Мультимодельная AI архитектура (GPT-5, Claude 4.5, Gemini, Grok)
- Маршрутизация задач на естественном языке
- Генерация кода в реальном времени с предпросмотром
- Автоматизация браузера с AI зрением
- Система верификации документов
- Возможности самооптимизации`
        },
        {
          id: 'code-generation',
          title: '⚡ AI Генерация Кода',
          content: `**Как использовать:**
1. Просто опишите идею приложения на естественном языке
2. Chimera автоматически генерирует full-stack код (React + FastAPI + MongoDB)
3. Мгновенный предпросмотр
4. Экспорт или изменение по необходимости

**Используемые модели:**
- Основная: Grok Beta (быстрая, оптимизирована для кода)
- Планирование: GPT-5 + Claude 3.5 Sonnet

**Возможности:**
- Предпросмотр кода в реальном времени
- Автоматическое управление зависимостями
- Интеграция с MongoDB
- Экспорт в GitHub или скачивание ZIP
- Сохранение сессий

**Примеры запросов:**
- "Создай todo приложение с drag-and-drop"
- "Сделай дашборд с графиками и диаграммами"
- "Построй чат с реалтайм сообщениями"`
        },
        {
          id: 'design-first',
          title: '🎨 Дизайн-Первый Подход',
          content: `**Как работает:**
1. Опишите визуальный дизайн приложения
2. AI генерирует детальную спецификацию дизайна
3. Визуальный валидатор проверяет дизайн
4. Вы утверждаете или корректируете
5. Код генерируется в соответствии с дизайном

**Используемые модели:**
- Генерация дизайна: Gemini 2.5 Nano Banana ($0.01/1M токенов)
- Визуальная валидация: Gemini 2.5 Nano Banana

**Преимущества:**
- UI соответствует требованиям до кодирования
- Экономичная визуальная модель
- Меньше итераций
- Профессиональный дизайн

**Пример:**
"Создай современный темный дашборд с боковым меню, карточками статистики и таблицей данных"`
        },
        {
          id: 'browser-automation',
          title: '🤖 Автоматизация Браузера',
          content: `**Как использовать:**
Просто опишите что хотите автоматизировать на естественном языке. Система автоматически определит что это задача автоматизации.

**Примеры:**
- "Зайди в Google и найди AI"
- "Перейди в Twitter и залогинься"
- "Заполни эту форму регистрации"
- "Нажми кнопку купить и оформи заказ"

**Как работает:**
1. AI классифицирует сообщение как задачу автоматизации
2. Агент планирования создает пошаговый план
3. Браузер открывается и выполняет шаги
4. Локальная визуальная модель находит элементы (БЕСПЛАТНО)
5. Проверяет каждое действие
6. Возвращает результаты

**Используемые модели:**
- Планирование: GPT-5 (сложная декомпозиция задач)
- Зрение: Локальная модель (БЕСПЛАТНО, быстрое определение элементов)
- Валидация: Nano Banana

**Возможности:**
- Команды на естественном языке
- Не нужны селекторы
- Валидация по скриншотам
- Контроль паузы/продолжения
- Детальное логирование

**Продвинутое:**
- Умный клик: находит элементы по описанию
- Умный ввод: интеллектуально заполняет формы
- Условия ожидания: адаптируется к загрузке страницы
- Восстановление от ошибок: повторы при сбое`
        },
        {
          id: 'document-verification',
          title: '📄 Верификация Документов',
          content: `**Как использовать:**
1. Загрузите изображение документа
2. Система анализирует тремя топовыми AI моделями
3. Получите консенсусный вердикт с показателем уверенности

**Используемые модели (Тройная Верификация):**
1. GPT-5: Глубокий анализ содержимого
2. Claude 4.5 Sonnet: Структурная верификация
3. Gemini 2.5 Flash Vision: Визуальная аутентичность

**Что обнаруживает:**
- AI-сгенерированный контент
- Подделки документов
- Манипуляции в Photoshop
- Несоответствие метаданных
- Поддельные подписи
- Фальшивые водяные знаки

**Результат:**
- Вероятность мошенничества (0-100%)
- Список красных флагов
- Индикаторы подлинности
- Уровень согласия моделей
- Детальный анализ от каждой модели

**Применение:**
- Проверка удостоверений
- Валидация контрактов
- Аутентификация сертификатов
- Обнаружение мошенничества с счетами
- Верификация юридических документов`
        },
        {
          id: 'self-improvement',
          title: '🧠 Система Самосовершенствования',
          content: `**Возможности:**
1. **Оптимизация Моделей**
   - Автоматически выбирает лучшие модели для каждой задачи
   - Баланс стоимости и качества
   - Использует БЕСПЛАТНЫЕ модели где возможно
   - Отслеживание затрат в реальном времени

2. **Анализ Кода**
   - Проверяет собственную кодовую базу
   - Находит проблемы безопасности
   - Обнаруживает узкие места производительности
   - Предлагает улучшения

3. **Автоматическая Оптимизация**
   - Применяет безопасные исправления автоматически
   - Перезагружает сервисы после изменений
   - Отслеживает историю оптимизаций
   - Возможность отката

**Используемые модели:**
- Анализ: Claude 3.5 Sonnet (отличное понимание кода)
- Оптимизация: GPT-5 или Claude 4.5

**Как использовать:**
1. Нажмите "Self-Improvement" в настройках
2. Просмотр текущих назначений моделей
3. Нажмите "Оптимизировать Модели" для автовыбора
4. Проверка здоровья системы
5. Анализ кода для улучшений
6. Применение оптимизаций

**Назначения Моделей:**
- Генерация кода: Grok Beta ($5/1M)
- Дизайн: Nano Banana ($0.01/1M) 
- Зрение автоматизации: Локальная модель (БЕСПЛАТНО)
- Планирование: GPT-5 ($15/1M)
- Верификация: Мультимодель`
        },
        {
          id: 'context-management',
          title: '🔄 Управление Контекстом',
          content: `**Умная Обработка Контекста:**
- Мониторинг использования токенов в реальном времени
- Автоматическое сжатие при приближении к лимиту
- Создание новых сессий со сжатым контекстом
- Передача важной информации

**Возможности:**
- Динамическое отслеживание окна контекста
- Специфичные лимиты модели (из OpenRouter)
- Автоматическое переключение сессий
- Сжатие контекста через AI
- Оптимизация затрат

**Визуальные Индикаторы:**
- Зеленый: Безопасно (<80% использования)
- Желтый: Предупреждение (80-90%)
- Красный: Критично (>90%)

**Как работает:**
1. Отслеживает токены для текущей модели
2. Сжимает старые сообщения при необходимости
3. Создает новую сессию при достижении лимита
4. Сохраняет ключевую информацию
5. Бесшовное продолжение

**Преимущества:**
- Никогда не теряется контекст разговора
- Оптимальное использование токенов
- Экономия средств
- Без ручного управления сессиями`
        },
        {
          id: 'session-management',
          title: '💾 Управление Сессиями',
          content: `**Возможности:**
- Автоматическое создание сессий
- Постоянное хранение в MongoDB
- Быстрое переключение сессий
- Поиск и фильтр сессий
- Экспорт истории сессий

**Сессия включает:**
- Все сообщения
- Сгенерированный код
- Дизайн-предложения
- Отслеживание затрат
- Временные метки

**Как использовать:**
1. Нажмите на логотип Chimera для просмотра сессий
2. Выберите предыдущую сессию для загрузки
3. Продолжайте с места остановки
4. Создавайте новую сессию в любое время

**Преимущества:**
- Никогда не теряется работа
- Организация проектов
- Просмотр истории
- Мультипроектный рабочий процесс`
        },
        {
          id: 'content-folder',
          title: '🗂️ Папка Контента',
          content: `**Что хранится:**
- Сгенерированные файлы кода
- Изображения дизайна
- Скриншоты
- Документы
- Результаты автоматизации

**Возможности:**
- Хранилище специфичное для сессии
- Организация по типу
- Быстрый предпросмотр
- Скачивание отдельных элементов
- Сохранение между сессиями

**Как получить доступ:**
- Нажмите иконку папки (🗂️) в заголовке
- Просмотр всего контента сессии
- Фильтр по типу
- Скачивание по необходимости

**Применение:**
- Архив сгенерированных приложений
- Сохранение итераций дизайна
- Экспорт результатов автоматизации
- Хранение анализа документов`
        },
        {
          id: 'personalization',
          title: '👤 Персонализация',
          content: `**AI Ассистент: Aria**
Ваш креативный компаньон, который:
- Говорит естественно (без "AI речи")
- Запоминает ваше имя
- Изучает предпочтения
- Адаптирует стиль общения

**Как работает:**
1. При первом запуске: Aria представляется
2. Она спрашивает ваше имя
3. Имя сохраняется в local storage
4. Персонализированное приветствие во всех сообщениях

**Преимущества:**
- Человекоподобное взаимодействие
- Комфортное общение
- Построение отношений
- Лучшее сотрудничество

**Примечание:**
Aria никогда не упоминает что она AI или модель - она общается как талантливый коллега, помогающий вам создавать удивительные вещи.`
        },
        {
          id: 'language',
          title: '🌐 Поддержка Языков',
          content: `**Поддерживаемые языки:**
- English (en)
- Русский (ru)

**Как переключить:**
1. Откройте Настройки (⚙️)
2. Выберите опцию Язык
3. Выберите предпочитаемый язык
4. Интерфейс обновится мгновенно

**Что переведено:**
- Все элементы UI
- Возможности платформы
- База знаний
- Сообщения об ошибках
- Подсказки

**Примечание:**
AI ответы автоматически адаптируются к вашему языку на основе ваших сообщений.`
        },
        {
          id: 'cost-optimization',
          title: '💰 Оптимизация Затрат',
          content: `**Стратегия:**
- БЕСПЛАТНЫЕ модели для простых задач (локальное зрение)
- Дешевые модели для дизайна ($0.01/1M)
- Среднего уровня для генерации кода ($5/1M)
- Премиум для сложного планирования ($15/1M)

**Текущие Затраты:**
- Браузерное зрение: БЕСПЛАТНО (локальная модель)
- Дизайн/Валидация: $0.01 за 1M токенов
- Генерация кода: $5.00 за 1M токенов
- Планирование: $15.00 за 1M токенов
- Тройная верификация: Переменная

**Советы по Экономии:**
1. Используйте зрение автоматизации (БЕСПЛАТНО)
2. Включите визуальный валидатор (дешево)
3. Позвольте системе оптимизировать модели
4. Мониторьте баланс OpenRouter

**Отслеживание в Реальном Времени:**
- Стоимость за сессию
- Общая стоимость платформы
- Затраты по моделям
- Баланс OpenRouter`
        },
        {
          id: 'tips-tricks',
          title: '💡 Советы и Лучшие Практики',
          content: `**Для Генерации Кода:**
- Будьте конкретны в функционале
- Упомяните tech stack если нужно
- Опишите требования UI/UX
- Используйте итеративное улучшение

**Для Автоматизации Браузера:**
- Используйте естественные описания
- Будьте ясны в цели
- Тестируйте сначала на простых задачах
- Просматривайте логи при проблемах

**Для Верификации Документов:**
- Используйте качественные изображения
- Включите полный документ
- Дождитесь всех 3 моделей
- Проверьте уровень согласия

**Общие Советы:**
1. Создавайте сессии для разных проектов
2. Используйте Папку Контента для организации
3. Мониторьте использование контекста
4. Позвольте Aria запомнить ваше имя
5. Изучайте возможности платформы
6. Проверяйте Базу Знаний при затруднениях

**Горячие Клавиши:**
- Ctrl/Cmd + Enter: Отправить сообщение
- Esc: Закрыть модальные окна
- Ctrl/Cmd + K: Поиск сессий`
        }
      ]
    }
  };

  const currentKB = knowledgeBase[language] || knowledgeBase.en;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-700 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Book className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">{currentKB.title}</h2>
            </div>
            <p className="text-sm text-gray-400">{currentKB.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {currentKB.sections.map((section) => (
              <div key={section.id} className="border border-gray-800 rounded-lg overflow-hidden bg-gray-900/50">
                <button
                  onClick={() => setExpandedSection(expandedSection === section.id ? null : section.id)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-800/50 transition-colors"
                >
                  <span className="text-white font-semibold">{section.title}</span>
                  {expandedSection === section.id ? (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  )}
                </button>
                
                {expandedSection === section.id && (
                  <div className="p-4 pt-0 border-t border-gray-800">
                    <div className="prose prose-invert prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed">
                        {section.content}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 bg-gray-900/50">
          <p className="text-xs text-gray-500 text-center">
            {language === 'ru' 
              ? '💡 Совет: Используйте Ctrl/Cmd + F для поиска по странице'
              : '💡 Tip: Use Ctrl/Cmd + F to search within this page'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBase;
