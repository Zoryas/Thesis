-- Operational support table for tracking deployment smoke-test results.
CREATE TABLE IF NOT EXISTS deployment_smoke_tests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_label VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSON NULL,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
