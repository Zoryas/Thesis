-- Initial schema placeholder for ReadWise.
-- This file is intentionally lightweight and is applied through the migration registry.
CREATE TABLE IF NOT EXISTS operational_health_checks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'ok'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
