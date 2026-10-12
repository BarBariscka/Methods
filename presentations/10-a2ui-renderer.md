# Лабораторная работа 10. A2UI Renderer: веб-интерфейс с динамическим UI

> | | |
> |---|---|
> | **Каталог** | `lab10-a2a-a2ui-renderer/` |
> | **Точка входа** | `src/App.tsx`, запуск `npm start` |
> | **Технологии** | TypeScript, React 19, Tailwind CSS, Zod, `@json-render/core`, `@json-render/react`, A2A (HTTP/SSE), Docker, nginx |
> | **Порт** | 3000 (переопределяется `PORT`) |
> | **Ориентировочное время** | 4–6 часов |

---

## 1. Цель работы

Разработать React-приложение с нативной поддержкой протокола
[A2UI](https://a2ui.org) — чат-интерфейс для взаимодействия с A2A-агентами, которые
возвращают **динамический UI** вместо текстового ответа.

---

## 2. Теоретическая часть

### Зачем агенту возвращать UI, а не текст

Текстовый ответ описывает результат. **UI-ответ показывает его**: таблицу платежей, форму
ввода параметров кредита, переключатели, графики. Пользователь сразу взаимодействует
с результатом, не описывая агенту следующий запрос.

| | Текстовый ответ | A2UI-ответ |
|---|---|---|
| Представление результата | Абзацы, списки | Компоненты: таблицы, формы, карточки |
| Следующий шаг | Написать запрос текстом | Нажать кнопку, заполнить поле |
| Скорость восприятия | Низкая | Высокая |

### Модель adjacency list

A2UI хранит компоненты в **плоском списке** (`Map<string, A2UIComponent>`), а дерево
связывается через ID-ссылки. Корневой компонент задаётся полем `rootId`.

Почему это эффективно для патч-обновлений:

1. **Адресация по ID** — обновление одного компонента требует изменения ровно одной записи
   в `Map`, а не обхода и пересборки всего дерева.
2. **Отсутствие вложенности** — нет глубокой рекурсии и сложного diff-а.
3. **Порядок не важен** — компоненты могут приходить в любом порядке: пока не указан `rootId`,
   рендерить нечего.

```
Компоненты (плоский список):
  { id: "root",    type: "Column",   children: ["card1"] }
  { id: "card1",   type: "Card",     children: ["title", "input1", "btn"] }
  { id: "title",   type: "Text",     text: "Параметры кредита" }
  { id: "input1",  type: "NumberInput", dataBinding: "/credit/amount" }
  { id: "btn",     type: "Button",   action: { name: "calculate", context: [...] } }

Дерево строится обходом от rootId = "root".
```

### Четыре типа сообщений A2UI

| Сообщение | Действие |
|---|---|
| `surfaceUpdate` | Добавить или обновить компоненты |
| `dataModelUpdate` | Обновить модель данных |
| `beginRendering` | Указать `root`, `surfaceId`, `catalogId` — с этого момента рендерить |
| `deleteSurface` | Очистить поверхность |

### Data binding

Свойства компонента бывают двух видов:

```jsonc
// Литеральное значение
{ "literalString": "Привет" }

// Привязка к пути в модели данных
{ "path": "/reservation/date" }   // значение из dataModel.reservation.date
```

Изменение поля в UI обновляет `dataModel` по этому пути, а при отправке действия (action)
значения собираются обратно и уходят агенту.

### Поток сообщений

1. Пользователь вводит текст в чат.
2. `A2AClient` отправляет сообщение серверу по протоколу A2A (SSE-стриминг).
3. Сервер возвращает ответ, который может содержать A2UI-данные.
4. `a2a-to-a2ui-adapter` конвертирует A2A-ответ в `A2UIMessage`.
5. Хук `useA2UI` обрабатывает сообщение и обновляет состояние.
6. `renderer.tsx` отрисовывает дерево компонентов от корневого ID.

---

## 3. Задание

1. Изучить `src/a2a/` (A2A-клиент, HTTP/SSE, адаптер и парсер сообщений), `src/a2ui/`
   (схемы, каталог компонентов, рендерер, хук) и `src/chat/` (компоненты чата, localStorage).
2. Запустить приложение: `npm install --legacy-peer-deps && npm start` (Node 18, порт 3000).
3. Подключиться к агенту из лаб. 2–6 через URL в шапке интерфейса.
4. Проверить рендеринг всех поддерживаемых компонентов: Text, Button, TextInput, NumberInput,
   DateTimeInput, Card, Row, Column, Image, Switch, Checkbox, Slider, Divider.
5. Проверить data binding и actions: изменение значений, отправка данных обратно агенту.
6. **Самостоятельное задание** (раздел 7): расширить рендерер новым компонентом.

---

## 4. Этапы выполнения

### Этап 1. Подготовка окружения

> ⚠️ Требуется **Node.js 18**. Более новые версии конфликтуют с create-react-app.

```bash
source ~/.nvm/nvm.sh
nvm use 18
cd lab10-a2a-a2ui-renderer
```

### Этап 2. Установка зависимостей

```bash
npm install --legacy-peer-deps
```

### Этап 3. Запуск приложения

```bash
npm start
```

Приложение будет доступно на http://localhost:3000.

Альтернативный запуск через Docker:

```bash
docker compose up --build           # порт 3000
PORT=8080 docker compose up --build # другой порт
```

Или создать `.env` в корне проекта:

```
PORT=8080
```

### Этап 4. Подключение к агенту

URL сервера A2A настраивается прямо в интерфейсе — в шапке страницы есть поле ввода.
Значение сохраняется в `localStorage` и переиспользуется между сессиями.

Ввести URL агента из лаб. 2–6, например
`http://localhost:10000 (локальный A2A-агент)`.

### Этап 5. Проверка компонентов

Проверить рендеринг всех компонентов каталога. В `src/a2ui/catalog.ts` зарегистрированы:

`Text`, `Button`, `DateTimeInput`, `NumberInput`, `TextInput`, `Column`, `Row`, `Card`,
`Image`, `Switch`, `Checkbox`, `CheckBox`, `Slider`, `Divider`, `MultipleChoice`,
`TextField`, `Icon`, `Video`, `AudioPlayer`, `Modal`, `List`, `Tabs`.

Для каждого зафиксировать скриншот в отчёте.

### Этап 6. Проверка data binding и actions

- Изменить значение в `NumberInput` — проверить, что `dataModel` обновился.
- Нажать `Button` с действием — проверить, что данные отправлены агенту
  и пришёл новый ответ с обновлённым UI.

### Этап 7. Самостоятельное задание

См. раздел 7.

### Этап 8. Сборка для продакшена

```bash
npm run build     # сборка для продакшена
npm test          # запуск тестов
```

---

## 5. Ключевые инженерные решения

### Состояние A2UI и разрешение привязок

```typescript
// src/a2ui/useA2UI.ts
export interface A2UIState {
  components: Map<string, A2UIComponent>;
  dataModel: Record<string, any>;
  rootId: string | null;
  surfaceId: string | null;
  catalogId: string | null;
  isLoading?: boolean;
}

/**
 * Resolve a BoundValue to its actual value.
 * If value has a path, resolve it from the dataModel;
 * otherwise return the literal value.
 */
function resolveBoundValue(boundValue: BoundValue,
                           dataModel: Record<string, any>): unknown {
  if (boundValue.path !== undefined) {
    const parts = boundValue.path.replace(/^\//, '').split('/');
    let result: any = dataModel;
    for (const part of parts) {
      if (result && typeof result === 'object' && part in result) {
        result = result[part];
      } else {
        return undefined;
      }
    }
    return unwrapTypedValue(result);
  }
  return boundValue.literalString
      ?? boundValue.literalNumber
      ?? boundValue.literalBoolean;
}
```

### Обработка сообщений A2UI

```typescript
const handleMessage = useCallback((message: A2UIMessage) => {
  if (message.surfaceUpdate) {
    setComponents(prev => {
      const next = new Map(prev);
      for (const comp of message.surfaceUpdate!.components) {
        next.set(comp.id, comp);            // добавить/обновить по id
      }
      return next;
    });
    // Инкремент версии — принудительный ремонт компонента в React
    setComponentVersions(prev => {
      const next = new Map(prev);
      for (const comp of message.surfaceUpdate!.components) {
        next.set(comp.id, (next.get(comp.id) || 0) + 1);
      }
      return next;
    });
  }

  if (message.dataModelUpdate) {
    setDataModel(prev => {
      const next = { ...prev };
      const path = message.dataModelUpdate!.path;
      if (path && path !== 'root') {
        const parts = path.replace(/^\//, '').split('/');
        let target = next;
        for (let i = 0; i < parts.length - 1; i++) {
          target[parts[i]] = target[parts[i]] || {};
          target = target[parts[i]];
        }
        unpackValueMap(message.dataModelUpdate!.contents,
                       target, parts[parts.length - 1]);
      } else {
        unpackValueMap(message.dataModelUpdate!.contents, next);
      }
      return next;
    });
  }

  if (message.beginRendering) {
    setRootId(message.beginRendering.root);          // ← с этого момента рендерим
    setSurfaceId(message.beginRendering.surfaceId || null);
    setCatalogId(message.beginRendering.catalogId || null);
  }

  if (message.deleteSurface) {
    setComponents(new Map());
    setRootId(null);
    setSurfaceId(null);
  }
}, []);
```

### Отправка действий агенту

```typescript
const handleAction = useCallback<A2UIActionCallback>((event) => {
  const { action, sourceComponentId } = event;

  if (client && action) {
    // Разрешаем значения контекста из привязок или литералов
    const resolvedContext: Record<string, unknown> = {};
    if (action.context) {
      for (const ctxItem of action.context) {
        resolvedContext[ctxItem.key] =
            resolveBoundValue(ctxItem.value, dataModel);
      }
    }

    const contextId = getContextId ? getContextId() : null;
    const messageId = `action-${Date.now()}`;
    onCreateAssistantMessage?.(messageId);   // плейсхолдер ответа
    setIsLoading(true);

    client.sendUserAction(
      action.name,          // имя действия
      resolvedContext,      // данные из dataModel
      surfaceId || '',      // обязателен по спецификации
      sourceComponentId,    // какой компонент вызвал
      messageId,
      contextId             // идентификатор контекста диалога
    ).catch((error) => {
      console.error('[useA2UI] Failed to send user action:', error);
      setIsLoading(false);
    });
  }

  if (customOnAction) customOnAction(event);
}, [client, getContextId, surfaceId, dataModel, customOnAction,
    setIsLoading, onCreateAssistantMessage]);
```

### Архитектура проекта

```
src/
  a2ui/                    # Ядро A2UI
    schemas.ts             # Zod-схемы типов сообщений A2UI
    catalog.ts             # Каталог компонентов (@json-render/core)
    renderer.tsx           # React-рендерер компонентов
    useA2UI.ts             # React-хук для управления состоянием A2UI
  a2a/                     # Клиент протокола A2A
    client.ts              # HTTP/SSE клиент
    types.ts               # Типы A2A-протокола
    a2a-to-a2ui-adapter.ts # Адаптер A2A → A2UI сообщений
    message-parser.ts      # Парсер SSE-сообщений
  chat/                    # UI чат-интерфейса
    ChatHistory.tsx
    ChatInput.tsx
    MessageBubble.tsx
    ServerConfig.tsx       # Поле URL агента в шапке
    LoadingScreen.tsx
    storage.ts             # Работа с localStorage
    types.ts
  App.tsx                  # Корневой компонент
```

### Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `PORT` | `3000` | Порт, на котором доступно приложение (при сборке через Docker) |

URL сервера A2A задаётся в интерфейсе и хранится в `localStorage`.

---

## 6. Самостоятельное задание

Расширить рендерер новым компонентом — например **`Table`** для отображения графиков платежей
из лаб. 1 / лаб. 9 — и продемонстрировать его отображение в чате.

**Шаги реализации:**

1. **Определить схему** таблицы в `src/a2ui/schemas.ts` (Zod): заголовки колонок,
   строки, необязательные действия.

2. **Зарегистрировать компонент** в каталоге `src/a2ui/catalog.ts`:

```typescript
Table: {
  props: {
    headers: z.array(z.string()),
    rows: z.array(z.array(z.union([BoundValue, z.string(), z.number()]))),
  },
  defaultValue: { headers: [], rows: [] },
  dataBinding: z.string(),
},
```

3. **Реализовать рендеринг** в `src/a2ui/renderer.tsx`: развернуть значения через
   `resolveBoundValue`, отрисовать `<table>` с поддержкой Tailwind-стилей.

4. **Подключить к агенту:** изменить системный промпт агента так, чтобы он возвращал
   компонент `Table` с графиком платежей из ответа MCP-инструмента
   `loan_schedule_annuity`.

5. **Продемонстрировать:** отправить запрос «рассчитай график кредита» и показать
   полученную таблицу в чате.

---

## 7. Контрольные вопросы

1. Что такое A2UI и зачем агенту возвращать UI, а не текст?
2. Как устроена модель adjacency list и почему она эффективна для патч-обновлений?
3. Как реализован data binding между компонентами и моделью данных
   (литералы и привязки по пути)?
4. Как actions возвращают данные на сервер агента и что такое `contextId` / `surfaceId`?
5. Зачем нужен инкремент `componentVersions` при обновлении компонента?
6. Как работает SSE-стриминг в `A2AClient` и чем отличается парсинг сообщений
   от обычного JSON-запроса?

---

## 8. Критерии приёмки

- [ ] Приложение запускается на Node 18, доступно на `localhost:3000`.
- [ ] URL агента настраивается в шапке и сохраняется в `localStorage`.
- [ ] Все поддерживаемые компоненты рендерятся корректно (скриншоты в отчёте).
- [ ] Data binding работает: изменение значения обновляет модель.
- [ ] Actions возвращают данные агенту и приходит обновлённый UI.
- [ ] Добавлен компонент `Table` и показан в чате (самостоятельное задание).
- [ ] Демонстрируется полный цикл: запрос → агент → A2UI-компоненты → взаимодействие → ответ.

---

## 9. Типичные ошибки и решение

| Проблема | Причина | Решение |
|---|---|---|
| Ошибка установки зависимостей | Конфликт версий peer-пакетов | Использовать флаг `npm install --legacy-peer-deps` |
| Не та версия Node | Требуется Node 18 | `source ~/.nvm/nvm.sh && nvm use 18` |
| Нет связи с агентом | Неверный URL или сетевая недоступность | Проверить URL в шапке, доступность агента, CORS |
| Компоненты не обновляются | React не перерендеривает тот же объект | Проверить инкремент `componentVersions` |
| UI не отрисовывается | Не пришёл `beginRendering` | Проверить порядок сообщений: `surfaceUpdate` → `beginRendering` |
| Значение поля пустое | Путь привязки не найден в `dataModel` | Проверить соответствие `path` структуре модели данных |
| Действие не отправляется | Не передан `surfaceId` | Передать `surfaceId || ''` — поле обязательно по спецификации |