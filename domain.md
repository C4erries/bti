# Доменная модель проекта «Умное БТИ»

Этот документ фиксирует целевую доменную модель. Любые изменения в предметной области нужно сначала согласовать здесь, а затем синхронизировать backend, frontend и OpenAPI.

## 1. Роли и пользователи

- **Роли**
  - Клиент — инициирует и сопровождает заказы.
  - Исполнитель — выполняет заказы, работает с планами, выездами и статусами.
  - Администратор — управляет пользователями, справочниками, заказами, AI‑правилами и журналом ошибок.

- **Сущности**
  - `User`
    - `id: UUID`
    - `email: str`
    - `password_hash: str`
    - `full_name: str | None`
    - `phone: str | None`
    - `is_admin: bool`
    - `is_superadmin: bool`
    - `is_blocked: bool`
    - `created_at`, `updated_at`
  - `ClientProfile`
    - один‑к‑одному с `User`;
    - доп. поля клиента (организация, ИП/физлицо, заметки).
  - `ExecutorProfile`
    - один‑к‑одному с `User`;
    - `department_code: str | None`
    - `experience_years: int | None`
    - `specialization: str | None`.

## 2. Справочники

- **District**
  - `code: str` — стабильный машинный код (например, `central`, `west`, `prikub`, `karasun`);
  - `name: str` — человекочитаемое название (например, «Центральный», «Западный», «Прикубанский», «Карасунский»);
  - `price_coef: float | None` — коэффициент для калькулятора.

- **HouseType**
  - `code: str` — машинный код (например, `panel`, `brick`);
  - `name: str` — название на русском («Панельный дом», «Кирпичный дом» и т.п.);
  - `description: str | None`;
  - `price_coef: float | None`.

- **Важно: сущности `Service` (справочник услуг) в домене больше нет**
  - Ранее:
    - существовали таблица/модель `Service`,
    - API `/services`, `/admin/services`,
    - поля `serviceCode`/`serviceTitle` в заказах и связанных DTO.
  - Сейчас:
    - отдельный каталог услуг не используется;
    - тип и сложность работ закодированы через параметры калькулятора (`calculatorInput`) и текст заказа;
    - все упоминания `Service` считаются техническим долгом и должны быть удалены в ходе рефакторинга.

## 3. Заказы

- **Order**
  - Идентификация и связь:
    - `id: UUID`
    - `client_id: UUID` → `User` (через `ClientProfile`)
  - Бизнес‑поля:
    - `status: OrderStatus` (например, `DRAFT`, `SUBMITTED`, `IN_PROGRESS`, `AWAITING_CLIENT_APPROVAL`, `COMPLETED`, `CANCELLED` и др.);
    - `title: str` — короткое название задачи;
    - `description: str | None` — подробное описание/пожелания клиента;
    - `address: str | None`;
    - `district_code: str | None` — FK на `District.code`;
    - `house_type_code: str | None` — FK на `HouseType.code`;
    - `complexity: str | None` — оценка сложности (опционально).
  - Стоимость и отдел:
    - `calculator_input: dict | None` — сырые данные калькулятора;
    - `estimated_price: float | None` — предварительная оценка;
    - `total_price: float | None` — финальная цена (может выставляться исполнителем/админом);
    - `current_department_code: str | None` — ответственный отдел (логика маршрутизации задаётся сервисом заказов).
  - Статусы и даты:
    - `ai_decision_status: str | None` — итоговое решение AI по перепланировке;
    - `ai_decision_summary: str | None` — краткое резюме;
    - `planned_visit_at: datetime | None`;
    - `completed_at: datetime | None`;
    - `created_at: datetime`;
    - `updated_at: datetime | None`.

- **OrderStatusHistory**
  - История изменения статусов:
    - `order_id: UUID`;
    - `status: OrderStatus`;
    - `old_status: str | None`;
    - `changed_by_id: UUID | None` — кто поменял статус;
    - `changed_at: datetime`;
    - `comment: str | None`.

## 4. План и файлы

- **OrderFile**
  - `id: UUID`
  - `order_id: UUID`
  - `sender_id: UUID | None`
  - `filename: str`
  - `path: str`
  - `created_at: datetime`.

- **Plan / OrderPlanVersion**
  - `OrderPlanVersion`:
    - `id: UUID`
    - `order_id: UUID`
    - `version_type: str` — `ORIGINAL` / `MODIFIED` / др. типы;
    - `plan: Plan`
    - `comment: str | None`
    - `created_by_id: UUID | None`
    - `created_at: datetime`.
  - `Plan` (см. `backend/app/schemas/plan.py`):
    - `meta`: размеры, единицы, масштаб, фон;
    - `elements`: список объектов 2D‑плана:
      - `wall` (стены, несущие/ненесущие, толщина, роли EXISTING/TO_DELETE/NEW/MODIFIED);
      - `zone` (функциональные зоны, связь с элементами);
      - далее — двери, окна, подписи (по мере внедрения);
      - `style` (опционально): цвет HEX или ссылка на текстуру для отрисовки стены/зоны.
    - `objects3d`: опциональный список 3D‑объектов для визуализации.
    - Contract: структура `Plan` совпадает с `3Dmodel_schema.json` (meta width/height/unit px, опциональные scale/background и ceiling_height_m, сегменты/полигоны/точки с openings у стен, objects3d с position/rotation/size и wallId/zoneId).

## 5. Чат и AI

- **Чат по заказу**
  - `OrderChatMessage`:
    - `id: UUID`
    - `chat_id: UUID`
    - `order_id: UUID | None`
    - `sender_id: UUID | None`
    - `sender_type: str | None` (client/executor/admin/ai)
    - `message_text: str`
    - `meta: dict | None`
    - `created_at: datetime`.

- **AI‑анализ**
  - `AiAnalysis`:
    - `id: UUID`
    - `order_id: UUID`
    - `decision_status: str` — итоговое решение (`UNKNOWN`, `ALLOWED`, `FORBIDDEN`, `NEEDS_APPROVAL` и т.п.);
    - `summary: str | None` — краткое описание;
    - `risks: list[AiRisk] | None`
    - доп. поля: предупреждения, рекомендации, сырое тело ответа модели.

## 6. Исполнители и календарь

- **ExecutorAssignment**
  - Связь заказа и исполнителя:
    - `order_id: UUID`
    - `executor_id: UUID`
    - `status: AssignmentStatus`
    - `assigned_at: datetime`
    - `assigned_by_user_id: UUID | None`.

- **ExecutorCalendarEvent**
  - Событие в календаре исполнителя:
    - `id: UUID`
    - `executor_id: UUID`
    - `order_id: UUID | None`
    - `title: str | None`
    - `description: str | None`
    - `start_time: datetime`
    - `end_time: datetime`
    - `location: str | None`
    - `status: CalendarStatus`
    - `created_at: datetime | None`.

## 7. Калькулятор стоимости

- **Общий принцип**
  - Стоимость заказа определяется:
    - округом (`districtCode` → `District.price_coef`);
    - типом дома (`houseTypeCode` → `HouseType.price_coef`);
    - параметрами калькулятора (`calculatorInput`).
  - Отдельная сущность «услуга» и её базовая цена не используются.

- **Структура `calculatorInput`**

```ts
interface CalculatorWorks {
  walls?: boolean;
  wet_zone?: boolean;
  doorways?: boolean;
}

interface CalculatorFeatures {
  basement?: boolean;
  join_apartments?: boolean;
}

interface CalculatorInput {
  area?: number;
  works?: CalculatorWorks;
  features?: CalculatorFeatures;
  urgent?: boolean;
  notes?: string;
}
```

- **PriceCalculatorInput (REST‑API `/calc/estimate`)**
  - `districtCode?: string | null`
  - `houseTypeCode?: string | null`
  - `calculatorInput?: CalculatorInput | null`

- **Инварианты**
  - Структура `CalculatorInput` одинакова:
    - при публичном расчёте (`/calc/estimate`);
    - при создании/редактировании заказа (`calculatorInput` поля `Order`).
  - Любое расширение калькулятора:
    - добавляет новые поля в `CalculatorInput` без поломки существующего контракта;
    - сопровождается обновлением `openapi.yaml`, фронта и, при необходимости, этого документа.

## 8. Что считается техническим долгом (target state vs current)

На момент написания:

- В коде ещё присутствуют:
  - модель и таблица `Service`;
  - API `/services`, `/admin/services`;
  - поля `service_code` / `serviceCode` / `serviceTitle` в моделях заказов и нескольких DTO/типах фронтенда.
- В доменной модели они **больше не считаются частью предметной области**:
  - при работе над кодом их нужно постепенно устранить,
  - вместо них использовать параметры калькулятора и текст заказа.

При добавлении новой функциональности:

- не вводить заново сущность «услуга» без явной причины и обсуждения;
- опираться на `Order`, `District`, `HouseType`, `Plan`, `CalculatorInput` и связанные сущности.
