-- Schema version 1: scientific source database in the release is read-only.
CREATE TABLE IF NOT EXISTS evas(id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
INSERT OR REPLACE INTO metadata VALUES ('schema_version','1');
PRAGMA user_version=1;
