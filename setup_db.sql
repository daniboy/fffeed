-- NOTICE: This file uses SQLite dialect, some changes might be required for other databases
-- NOTICE: This file has to be updated manually if the code changes

CREATE TABLE change (
  id            INTEGER PRIMARY KEY NOT NULL,
  event_time    TEXT,
  event_type    TEXT,
  event_content TEXT
);

CREATE TABLE friend (
  id   INTEGER PRIMARY KEY NOT NULL,
  name TEXT
);

CREATE TABLE variable (
  key   TEXT PRIMARY KEY NOT NULL,
  value TEXT
);
