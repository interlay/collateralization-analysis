class CoingeckoRates:
    def __init__(self, warehouse_db):
        self.warehouse_db = warehouse_db
        self.name = "coingecko_usd_rates"

    def create(self):
        """
        Stores the usdRates for each token in the human denomination (e.g., in BTC, ETH, DOT, ...).
        """
        with self.warehouse_db(self.name) as db:
            db.execute("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                symbol TEXT NOT NULL,
                coingecko_id TEXT NOT NULL,
                vs_currency TEXT NOT NULL,
                rate NUMERIC NOT NULL
            );
            """.format(self.name))

    def insert(self, timestamp, coingecko_rates):
        for symbol, rate in coingecko_rates.items():
            coingecko_id = rate["coingeckoId"]
            usd_rate = rate["usdRate"]

            with self.warehouse_db() as db:
                db.execute("""
                INSERT INTO {} (timestamp, symbol, coingecko_id, vs_currency, rate)
                VALUES (%s, %s, %s, 'usd', %s);
                """.format(self.name), (timestamp, symbol, coingecko_id, usd_rate))

    def execute(self, statement):
        with self.warehouse_db() as db:
            db.execute("{}".format(statement))

            return db.fetchall()

    def drop(self):
        with self.warehouse_db() as db:
            db.execute("""
            DROP TABLE IF EXISTS {};
            """.format(self.name))
