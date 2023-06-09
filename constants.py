from enum import Enum


class ToBaseDecimals(Enum):
    DOLLAR = (0,)
    BITCOIN = (8,)
    POLKADOT = (10,)
    KUSAMA = (12,)
    KINTSUGI = (12,)
    PERCENTAGE = (18,)
    LP_TOKEN = (18,)
    PLANK = (18,)

    def get_decimals(self):
        return self.value[0]


class Thresholds(Enum):
    SECURE = "SecureCollateralThreshold"
    PREMIUM = "PremiumRedeemThreshold"
    LIQUIDATION = "LiquidationCollateralThreshold"

    def get_threshold(self):
        return self.value


ASSETS = {
    "ForeignAsset": {
        1: {"decimals": 6, "symbol": "USDT", "usdRate": 1.0005e-06},
        2: {"decimals": 18, "symbol": "MOVR", "usdRate": 9.648910000000001e-18},
        3: {"decimals": 12, "symbol": "LKSM", "usdRate": 4.52483e-12},
        4: {"decimals": 12, "symbol": "VKSM", "usdRate": 4.0022000000000004e-13},
        5: {"decimals": 12, "symbol": "SKSM", "usdRate": 6.578000000000001e-14},
    },
    "LendToken": {
        1: {"Token": "KBTC", "usdRate": 4.647754196000001e-06},
        2: {"Token": "KSM", "usdRate": 7.297498e-13},
        3: {"ForeignAsset": 1, "usdRate": 2.0010000000000002e-08},
        4: {"ForeignAsset": 2, "usdRate": 1.9297820000000001e-19},
    },
    "LpToken": {
        "({'Token': 'KBTC'}, {'ForeignAsset': 1})": {
            "Tokens": ({"Token": "KBTC"}, {"ForeignAsset": 1}),
            "usdRate": 3.0497218146769328e-05,
        },
        "({'Token': 'KBTC'}, {'ForeignAsset': 2})": {
            "Tokens": ({"Token": "KBTC"}, {"ForeignAsset": 2}),
            "usdRate": 9.478499170245455e-11,
        },
        "({'Token': 'KINT'}, {'ForeignAsset': 2})": {
            "Tokens": ({"Token": "KINT"}, {"ForeignAsset": 2}),
            "usdRate": 6.316947102149352e-15,
        },
        "({'Token': 'KSM'}, {'Token': 'KBTC'})": {
            "Tokens": ({"Token": "KSM"}, {"Token": "KBTC"}),
            "usdRate": 1.841662269519491e-07,
        },
    },
    "StableLpToken": {
        0: {
            "Tokens": [{"ForeignAsset": 3}, {"ForeignAsset": 4}, {"ForeignAsset": 5}],
            "usdRate": 3.772390867211666e-18,
        },
        1: {
            "Tokens": [
                {"Token": "KSM"},
                {"ForeignAsset": 3},
                {"ForeignAsset": 4},
                {"ForeignAsset": 5},
            ],
            "usdRate": 8.467749775238545e-18,
        },
    },
    "Token": {
        "DOT": {"decimals": 10, "symbol": "DOT", "usdRate": 6.87413e-10},
        "IBTC": {"decimals": 8, "symbol": "IBTC", "usdRate": 0.00017940316620000001},
        "INTR": {"decimals": 10, "symbol": "INTR", "usdRate": 2.337e-12},
        "KBTC": {"decimals": 8, "symbol": "KBTC", "usdRate": 0.00023238770980000002},
        "KINT": {"decimals": 12, "symbol": "KINT", "usdRate": 1.0336399999999998e-12},
        "KSM": {"decimals": 12, "symbol": "KSM", "usdRate": 3.648749e-11},
    },
}
