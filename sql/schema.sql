CREATE TABLE IF NOT EXISTS cpd_incidents (
    id BIGINT PRIMARY KEY,
    date_time TIMESTAMP NOT NULL,
    type TEXT NOT NULL,
    subtype TEXT,
    location TEXT,
    description TEXT,
    last_updated TIMESTAMP,

    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    second INTEGER NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cpd_date_time
    ON cpd_incidents(date_time);

CREATE INDEX IF NOT EXISTS idx_cpd_type
    ON cpd_incidents(type);

CREATE INDEX IF NOT EXISTS idx_cpd_subtype
    ON cpd_incidents(subtype);

CREATE INDEX IF NOT EXISTS idx_cpd_location
    ON cpd_incidents(location);

CREATE INDEX IF NOT EXISTS idx_cpd_year_month
    ON cpd_incidents(year, month);

CREATE INDEX IF NOT EXISTS idx_cpd_hour
    ON cpd_incidents(hour);
