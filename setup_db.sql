-- OneDesk MySQL Setup
-- Run once after installing MySQL:
--   mysql -u root -p < setup_db.sql

CREATE DATABASE IF NOT EXISTS onedesk
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE onedesk;

CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(36)  PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id          VARCHAR(36)  PRIMARY KEY,
    user_id     VARCHAR(36)  NOT NULL,
    title       VARCHAR(200) DEFAULT '',
    description TEXT,
    category    VARCHAR(50)  DEFAULT 'Personal',
    tags        JSON,
    color       VARCHAR(20)  DEFAULT 'violet',
    pinned      TINYINT(1)   DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id          VARCHAR(36)  PRIMARY KEY,
    user_id     VARCHAR(36)  NOT NULL,
    title       VARCHAR(200) DEFAULT '',
    description TEXT,
    priority    VARCHAR(20)  DEFAULT 'Medium',
    status      VARCHAR(30)  DEFAULT 'Todo',
    category    VARCHAR(50)  DEFAULT 'Personal',
    due_date    DATE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id          VARCHAR(36)  PRIMARY KEY,
    user_id     VARCHAR(36)  NOT NULL,
    title       VARCHAR(200) DEFAULT '',
    date        DATE,
    time        VARCHAR(10)  DEFAULT '',
    description TEXT,
    reminder    TINYINT(1)   DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
