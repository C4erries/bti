-- Logical database schema for "Умное БТИ"
-- This file is for documentation/overview only and may not exactly match any specific SQL dialect.

-- Users and profiles

CREATE TABLE users (
    id              UUID            PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    full_name       VARCHAR(255),
    phone           VARCHAR(50),
    is_admin        BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL,
    updated_at      TIMESTAMPTZ     NOT NULL
);

CREATE TABLE client_profiles (
    user_id             UUID            PRIMARY KEY,
    organization_name   VARCHAR(255),
    is_legal_entity     BOOLEAN         NOT NULL DEFAULT FALSE,
    notes               VARCHAR(500),
    CONSTRAINT fk_client_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE executor_profiles (
    user_id         UUID            PRIMARY KEY,
    department_code VARCHAR(50),
    experience_years INTEGER,
    specialization  VARCHAR(255),
    CONSTRAINT fk_executor_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_executor_profiles_department
        FOREIGN KEY (department_code) REFERENCES departments(code)
);

-- Directories

CREATE TABLE departments (
    code        VARCHAR(50)     PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    description TEXT
);

CREATE TABLE services (
    code                INTEGER         PRIMARY KEY,
    title               VARCHAR(255)    NOT NULL,
    description         TEXT,
    department_code     VARCHAR(50),
    base_price          DOUBLE PRECISION,
    base_duration_days  INTEGER,
    required_docs       JSON,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_services_department
        FOREIGN KEY (department_code) REFERENCES departments(code)
);

CREATE TABLE districts (
    code        VARCHAR(50)     PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    price_coef  DOUBLE PRECISION DEFAULT 1.0
);

CREATE TABLE house_types (
    code        VARCHAR(50)     PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    description TEXT,
    price_coef  DOUBLE PRECISION DEFAULT 1.0
);

-- Orders and related entities

CREATE TABLE orders (
    id                      UUID            PRIMARY KEY,
    client_id               UUID            NOT NULL,
    service_code            INTEGER         NOT NULL,
    current_department_code VARCHAR(50),
    department_code         VARCHAR(50),
    district_code           VARCHAR(50),
    house_type_code         VARCHAR(50),
    title                   VARCHAR(255)    NOT NULL,
    description             TEXT,
    address                 VARCHAR(255),
    area                    DOUBLE PRECISION,
    complexity              VARCHAR(20),
    status                  VARCHAR(32)     NOT NULL, -- enum OrderStatus
    calculator_input        JSON,
    estimated_price         DOUBLE PRECISION,
    total_price             DOUBLE PRECISION,
    ai_decision_status      VARCHAR(100),
    ai_decision_summary     TEXT,
    planned_visit_at        TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ     NOT NULL,
    updated_at              TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_orders_client
        FOREIGN KEY (client_id) REFERENCES users(id),
    CONSTRAINT fk_orders_service
        FOREIGN KEY (service_code) REFERENCES services(code),
    CONSTRAINT fk_orders_current_department
        FOREIGN KEY (current_department_code) REFERENCES departments(code),
    CONSTRAINT fk_orders_department
        FOREIGN KEY (department_code) REFERENCES departments(code),
    CONSTRAINT fk_orders_district
        FOREIGN KEY (district_code) REFERENCES districts(code),
    CONSTRAINT fk_orders_house_type
        FOREIGN KEY (house_type_code) REFERENCES house_types(code)
);

CREATE TABLE order_status_history (
    id              UUID            PRIMARY KEY,
    order_id        UUID            NOT NULL,
    status          VARCHAR(32)     NOT NULL, -- enum OrderStatus
    comment         TEXT,
    changed_by_id   UUID,
    created_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_order_status_history_order
        FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_status_history_user
        FOREIGN KEY (changed_by_id) REFERENCES users(id)
);

CREATE TABLE order_files (
    id              UUID            PRIMARY KEY,
    order_id        UUID            NOT NULL,
    filename        VARCHAR(255)    NOT NULL,
    path            VARCHAR(500)    NOT NULL,
    description     TEXT,
    uploaded_by_id  UUID,
    created_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_order_files_order
        FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_files_user
        FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
);

CREATE TABLE order_plan_versions (
    id              UUID            PRIMARY KEY,
    order_id        UUID            NOT NULL,
    version_type    VARCHAR(20)     NOT NULL, -- ORIGINAL / MODIFIED
    plan            JSON            NOT NULL,
    is_applied      BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_order_plan_versions_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Chat threads and messages

CREATE TABLE chat_threads (
    id              UUID            PRIMARY KEY,
    client_id       UUID            NOT NULL,
    order_id        UUID,
    service_code    INTEGER,
    title           VARCHAR(255)    NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL,
    updated_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_chat_threads_client
        FOREIGN KEY (client_id) REFERENCES users(id),
    CONSTRAINT fk_chat_threads_order
        FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_chat_threads_service
        FOREIGN KEY (service_code) REFERENCES services(code)
);

CREATE TABLE order_chat_messages (
    id              UUID            PRIMARY KEY,
    chat_id         UUID            NOT NULL,
    order_id        UUID,
    sender_id       UUID,
    sender_type     VARCHAR(20),
    message_text    TEXT            NOT NULL,
    meta            JSON,
    created_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_order_chat_messages_chat
        FOREIGN KEY (chat_id) REFERENCES chat_threads(id),
    CONSTRAINT fk_order_chat_messages_order
        FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_order_chat_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)
);

-- Executor assignments and calendar

CREATE TABLE executor_assignments (
    id              UUID            PRIMARY KEY,
    order_id        UUID            NOT NULL,
    executor_id     UUID            NOT NULL,
    assigned_by_id  UUID,
    status          VARCHAR(32)     NOT NULL, -- enum AssignmentStatus
    assigned_at     TIMESTAMPTZ     NOT NULL,
    updated_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_executor_assignments_order
        FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_executor_assignments_executor
        FOREIGN KEY (executor_id) REFERENCES users(id),
    CONSTRAINT fk_executor_assignments_assigned_by
        FOREIGN KEY (assigned_by_id) REFERENCES users(id)
);

CREATE TABLE executor_calendar_events (
    id              UUID            PRIMARY KEY,
    executor_id     UUID            NOT NULL,
    order_id        UUID,
    title           VARCHAR(255),
    description     TEXT,
    start_time      TIMESTAMPTZ     NOT NULL,
    end_time        TIMESTAMPTZ     NOT NULL,
    status          VARCHAR(32)     NOT NULL, -- enum CalendarStatus
    location        VARCHAR(255),
    notes           TEXT,
    created_at      TIMESTAMPTZ     NOT NULL,
    CONSTRAINT fk_executor_calendar_events_executor
        FOREIGN KEY (executor_id) REFERENCES users(id),
    CONSTRAINT fk_executor_calendar_events_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
);

