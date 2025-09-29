-- Initialize Kastoma Database
-- This script runs when the MySQL container starts for the first time

-- Create additional database configurations if needed
CREATE DATABASE IF NOT EXISTS kastoma_test;

-- Grant permissions to the user for test database
GRANT ALL PRIVILEGES ON kastoma_test.* TO 'kastoma_user'@'%';

-- Ensure the main user has full privileges
GRANT ALL PRIVILEGES ON kastoma_db.* TO 'kastoma_user'@'%';

-- Flush privileges to ensure changes take effect
FLUSH PRIVILEGES;

-- Set some MySQL configurations for better performance
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';