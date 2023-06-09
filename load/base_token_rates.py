from const import LP_TOKEN_DECIMALS


class BaseTokenRates():
    def __init__(self, warehouse_db, network):
        self.warehouse_db = warehouse_db
        tablename = "base_denomination_usd_rates"
        self.tablename = "{}_{}".format(network, tablename)

    def create(self):
        """
        Stores the usdRates for each token in the base denomination.
        As LP tokens and LendTokens have hard-coded rates, it is
        easier to work with the base denominations rather than
        working with the "human-friendly" denominations.
        """
        with self.warehouse_db(self.tablename) as db:
            db.execute("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                token_type TEXT NOT NULL,
                token_identifier TEXT NOT NULL,
                decimals NUMERIC,
                symbol TEXT,
                vs_currency TEXT NOT NULL,
                rate NUMERIC NOT NULL
            );
            """.format(self.tablename))

    def insert(self, timestamp, mapped_exchange_rates):
        with self.warehouse_db() as db:
            for token_type, token_data in mapped_exchange_rates.items():
                for token_identifier, data in token_data.items():
                    print("token_type: {}, token_identifier: {}, data: {}".format(token_type, token_identifier, data))
                    if "symbol" not in data:
                        data["symbol"] = "NULL"
                    if "decimals" not in data:
                        if token_type == "LpToken":
                            data["decimals"] = LP_TOKEN_DECIMALS
                        elif token_type == "StableLpToken":
                            data["decimals"] = LP_TOKEN_DECIMALS
                        else:
                            data["decimals"] = 0

                    if token_type == "LpToken" or token_type == "StableLpToken":
                        token_identifier = token_identifier.replace("'", "''")

                    db.execute("""
                    INSERT INTO {} (timestamp, token_type, token_identifier, decimals, symbol, vs_currency, rate)
                    VALUES ('{}', '{}', '{}', '{}', '{}', 'usd', '{}');
                    """.format(
                        self.tablename,
                        timestamp,
                        token_type,
                        token_identifier,
                        data["decimals"],
                        data["symbol"],
                        data["usdRate"],
                    ))

    def execute(self, statement):
        with self.warehouse_db() as db:
            db.execute("{}".format(statement))

            return db.fetchall()

    def drop(self):
        with self.warehouse_db() as db:
            db.execute("""
            DROP TABLE IF EXISTS {};
            """.format(self.tablename))
