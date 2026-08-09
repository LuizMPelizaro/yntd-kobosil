CREATE TABLE IF NOT EXISTS users (
  id_user INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(100),
  email VARCHAR(100) NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS markets (
  id_market INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  market_name VARCHAR(50) NOT NULL UNIQUE,
  country VARCHAR(50),
  currency VARCHAR(50),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (market_name, country)
);

CREATE TABLE IF NOT EXISTS stock_types (
  id_type INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  type_name VARCHAR(50) NOT NULL,
  sub_type_name VARCHAR(50),
  UNIQUE (type_name, sub_type_name)
);

CREATE TABLE IF NOT EXISTS stocks (
  id_stock INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  stock_code VARCHAR(20) NOT NULL,
  stock_name VARCHAR(150) NOT NULL,
  sector VARCHAR(50),
  subsector VARCHAR(50),
  logo_url VARCHAR(200),
  is_active BOOLEAN NOT NULL DEFAULT true,
  id_market INTEGER NOT NULL,
  id_type INTEGER NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_stocks_market
    FOREIGN KEY (id_market) REFERENCES markets(id_market),
  CONSTRAINT fk_stocks_type
    FOREIGN KEY (id_type) REFERENCES stock_types(id_type)
);

CREATE TABLE IF NOT EXISTS stock_transactions (
  id_transaction INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_user INTEGER NOT NULL,
  id_stock INTEGER NOT NULL,
  transaction_type VARCHAR(4) NOT NULL,
  quantity NUMERIC(18,6) NOT NULL,
  price NUMERIC(18,4) NOT NULL,
  transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (transaction_type IN ('BUY', 'SELL')),
  CHECK (quantity > 0),
  CHECK (price > 0),
  CONSTRAINT fk_transactions_user
    FOREIGN KEY (id_user) REFERENCES users(id_user),
  CONSTRAINT fk_transactions_stock
    FOREIGN KEY (id_stock) REFERENCES stocks(id_stock)
);

CREATE UNIQUE INDEX idx_stocks_code ON stocks(stock_code);
CREATE INDEX idx_stocks_market ON stocks(id_market);
CREATE INDEX idx_stocks_type ON stocks(id_type);
CREATE INDEX idx_transactions_user ON stock_transactions(id_user);
CREATE INDEX idx_transactions_stock ON stock_transactions(id_stock);
CREATE INDEX idx_transactions_user_date ON stock_transactions(id_user, transaction_date);

ALTER TABLE stock_transactions REPLICA IDENTITY FULL;
ALTER TABLE stocks REPLICA IDENTITY FULL;