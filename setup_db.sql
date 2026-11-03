-- OneDesk MySQL 8.x schema
-- Run with: mysql -u root -p < setup_db.sql
-- This script is safe on a fresh database and does not drop existing objects.
-- Existing tables are not altered by CREATE TABLE IF NOT EXISTS; back up and
-- plan a separate migration before applying this schema to an older database.
--
-- IMPORTANT: because category deletion is RESTRICTed while notes/tasks refer
-- to it, delete a user explicitly in this order inside one transaction:
-- notes, tasks, events, tags, categories, then users. Deleting notes/tags
-- cascades their note_tags rows. Do not rely on DELETE FROM users to cascade
-- through categories: category RESTRICT is intentionally preserved.

CREATE DATABASE IF NOT EXISTS onedesk
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE onedesk;

CREATE TABLE IF NOT EXISTS users (
    id            CHAR(36)      NOT NULL,
    name          VARCHAR(100)  NOT NULL,
    email         VARCHAR(254)  NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    avatar_path   VARCHAR(1024) NOT NULL DEFAULT '',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    CONSTRAINT chk_users_password_hash CHECK (
        BINARY password_hash LIKE BINARY '$argon2id$%'
        OR BINARY password_hash LIKE BINARY '$2a$%'
        OR BINARY password_hash LIKE BINARY '$2b$%'
        OR BINARY password_hash LIKE BINARY '$2y$%'
    )
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS categories (
    id            CHAR(36)     NOT NULL,
    user_id       CHAR(36)     NOT NULL,
    category_type VARCHAR(10)  NOT NULL,
    name          VARCHAR(100) NOT NULL,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_categories_user_type_name (user_id, category_type, name),
    UNIQUE KEY uq_categories_id_user_type (id, user_id, category_type),
    -- Categories must exist before notes/tasks; category_id is intentionally
    -- NOT NULL so every item has a user-owned, module-specific category.
    CONSTRAINT chk_categories_type CHECK (BINARY category_type IN ('note', 'task')),
    CONSTRAINT fk_categories_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS notes (
    id          CHAR(36)     NOT NULL,
    user_id     CHAR(36)     NOT NULL,
    category_id CHAR(36)     NOT NULL,
    category_type VARCHAR(10) NOT NULL DEFAULT 'note',
    title       VARCHAR(200) NOT NULL DEFAULT '',
    description TEXT         NULL,
    color       VARCHAR(20)  NOT NULL DEFAULT 'violet',
    pinned      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_notes_id_user (id, user_id),
    KEY ix_notes_user_pinned_created (user_id, pinned, created_at),
    KEY ix_notes_user_category (user_id, category_id),
    CONSTRAINT chk_notes_category_type CHECK (BINARY category_type = 'note'),
    CONSTRAINT chk_notes_color CHECK (BINARY color IN ('violet', 'cyan', 'green', 'amber', 'rose')),
    CONSTRAINT fk_notes_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_notes_category FOREIGN KEY (category_id, user_id, category_type)
        REFERENCES categories (id, user_id, category_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS tasks (
    id          CHAR(36)     NOT NULL,
    user_id     CHAR(36)     NOT NULL,
    category_id CHAR(36)     NOT NULL,
    category_type VARCHAR(10) NOT NULL DEFAULT 'task',
    title       VARCHAR(200) NOT NULL DEFAULT '',
    description TEXT         NULL,
    priority    VARCHAR(10)  NOT NULL DEFAULT 'Medium',
    status      VARCHAR(20)  NOT NULL DEFAULT 'Todo',
    due_date    DATE         NULL,
    completed_at DATE        NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_tasks_user_status_due (user_id, status, due_date),
    KEY ix_tasks_user_category (user_id, category_id),
    KEY ix_tasks_user_due (user_id, due_date),
    CONSTRAINT chk_tasks_category_type CHECK (BINARY category_type = 'task'),
    CONSTRAINT chk_tasks_priority CHECK (BINARY priority IN ('High', 'Medium', 'Low')),
    CONSTRAINT chk_tasks_status CHECK (BINARY status IN ('Todo', 'In Progress', 'Completed')),
    CONSTRAINT fk_tasks_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_tasks_category FOREIGN KEY (category_id, user_id, category_type)
        REFERENCES categories (id, user_id, category_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS events (
    id          CHAR(36)     NOT NULL,
    user_id     CHAR(36)     NOT NULL,
    title       VARCHAR(200) NOT NULL DEFAULT '',
    event_date  DATE         NOT NULL,
    event_time  TIME         NOT NULL,
    description TEXT         NULL,
    reminder    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_events_user_date_time (user_id, event_date, event_time),
    CONSTRAINT fk_events_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS tags (
    id         CHAR(36)     NOT NULL,
    user_id    CHAR(36)     NOT NULL,
    name       VARCHAR(100) NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tags_user_name (user_id, name),
    UNIQUE KEY uq_tags_id_user (id, user_id),
    CONSTRAINT fk_tags_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS note_tags (
    note_id    CHAR(36) NOT NULL,
    tag_id     CHAR(36) NOT NULL,
    user_id    CHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (note_id, tag_id),
    KEY ix_note_tags_note_user (note_id, user_id),
    KEY ix_note_tags_tag_user (tag_id, user_id),
    CONSTRAINT fk_note_tags_note_user FOREIGN KEY (note_id, user_id)
        REFERENCES notes (id, user_id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_note_tags_tag_user FOREIGN KEY (tag_id, user_id)
        REFERENCES tags (id, user_id) ON UPDATE RESTRICT ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
