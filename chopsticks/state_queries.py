from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface.base import QueryMapResult
from typing import Dict, List


from data.data_request import ToBaseDecimals, Token


class ChainGeneral(SubstrateInterface):
    def __init__(self):
        super().__init__(url="ws://localhost:8000")
        self.keypair = Keypair.create_from_uri("//Alice")

    def get_thresholds(self) -> None:
        self.thresholds = {
            "SecureCollateralThreshold": None,
            "PremiumRedeemThreshold": None,
            "LiquidationCollateralThreshold": None,
        }

        for key in self.thresholds.keys():
            self.thresholds[key] = self.query_map("VaultRegistry", key)

    def thresholds(self) -> Dict[str, QueryMapResult]:
        return self.thresholds

    def threshold(self, threshold_type: str, collateral: Token) -> float:
        """Returns the value for a specific threshold and collateral token.

        Args:
            threshold_type (str): Threshold to return
            collateral (str): The token to which the threshold belongs

        Returns:
            float: Threshold numbers as float. E.g. a return value of 1.8 equals 180%
        """

        for k, v in self.thresholds[threshold_type]:
            if k.value["collateral"].get("Token") == collateral.ticker:
                return v.value / 10 ** ToBaseDecimals.PERCENTAGE.get_decimals()

    def get_total_stake(self):
        self.total_stakes = self.query_map("VaultStaking", "TotalCurrentStake", [0])

    def vault_stakes(self, collateral: Token) -> Dict:
        stakes = {}
        for k, v in self.total_stakes:
            if (
                k.value["currencies"]["collateral"].get("Token") == collateral.ticker
            ) and (v.value != 0):
                stakes[k.value["account_id"]] = v.value / 10 ** (
                    collateral.decimals + ToBaseDecimals.PLANK.get_decimals()
                )
        return stakes

    def get_registered_vaults(self):
        self.vaults = self.query_map("VaultRegistry", "Vaults")

    def vaults_issuance(self, collateral: Token) -> Dict:
        issuance = {}
        for k, v in self.vaults:
            if (
                k.value["currencies"]["collateral"].get("Token") == collateral.ticker
            ) and (v.value["issued_tokens"] != 0):
                issuance[k.value["account_id"]] = (
                    v.value["issued_tokens"]
                    / 10 ** ToBaseDecimals.BITCOIN.get_decimals()
                )
        return issuance

    def update_collateral_ratios(
        self, collateral: Token, collateral_token_price: float, debt_token_price: float
    ) -> None:
        if not hasattr(self, "collateral_ratios"):
            self.collateral_ratios = {}
        if collateral.ticker not in self.collateral_ratios.keys():
            self.collateral_ratios[collateral.ticker] = {}

        for k, v in self.vaults_issuance(collateral).items():
            self.collateral_ratios[collateral.ticker][k] = (
                self.vault_stakes(collateral)[k] * collateral_token_price
            ) / (v * debt_token_price)

    def fund_account(
        self,
        token_amounts,
        account_id: str = None,
    ) -> None:
        calls = []

        for token, amount in token_amounts.items():
            calls.append(
                self.compose_call(
                    call_module="Tokens",
                    call_function="set_balance",
                    call_params={
                        "who": self.keypair.ss58_address
                        if account_id is None
                        else account_id,
                        "currency_id": {"Token": token.ticker},
                        "new_free": amount,
                        "new_reserved": 0,
                    },
                )
            )

        batched_call = self.compose_call(
            call_module="Utility", call_function="batch", call_params={"calls": calls}
        )

        sudo_call = self.compose_call("Sudo", "sudo", {"call": batched_call})

        extrinsic = self.create_signed_extrinsic(call=sudo_call, keypair=self.keypair)

        try:
            receipt = self.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            print(
                'Extrinsic "{}" included in block "{}"'.format(
                    receipt.extrinsic_hash, receipt.block_hash
                )
            )

            if receipt.is_success:

                print("✅ Success, triggered events:")
                for event in receipt.triggered_events:
                    print(f"* {event.value}")

            else:
                print("⚠️ Extrinsic Failed: ", receipt.error_message)

        except SubstrateRequestException as e:
            print("Failed to send: {}".format(e))

    ##########################
    # DEPRICATED
    def get_oracle_prices(self):
        return None

    def get_authorized_oracle_addresses(self):
        oracles = self.query_map("Oracle", "AuthorizedOracles")
        return [str(k) for k, v in oracles]

    def remove_oracles(self):
        oracle_addresses = self.get_authorized_oracle_addresses()
        calls = []
        for oracle_address in oracle_addresses:
            calls.append(
                self.compose_call(
                    call_module="Oracle",
                    call_function="remove_authorized_oracle",
                    call_params={"account_id": oracle_address},
                )
            )

        batched_call = self.compose_call(
            call_module="Utility", call_function="batch", call_params={"calls": calls}
        )

        sudo_call = self.compose_call("Sudo", "sudo", {"call": batched_call})

        extrinsic = self.create_signed_extrinsic(call=sudo_call, keypair=self.keypair)

        try:
            receipt = self.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            print(
                'Extrinsic "{}" included in block "{}"'.format(
                    receipt.extrinsic_hash, receipt.block_hash
                )
            )

            if receipt.is_success:

                print("✅ Success, triggered events:")
                for event in receipt.triggered_events:
                    print(f"* {event.value}")

            else:
                print("⚠️ Extrinsic Failed: ", receipt.error_message)

        except SubstrateRequestException as e:
            print("Failed to send: {}".format(e))

    # TODO: Complete this method if needed.
    def set_oracle_price(self, currency_id: str, symbol: str, value: int):
        self.compose_call(
            call_module="Oracle",
            call_function="FeedValues",
            call_params={
                "values": [
                    (
                        {
                            "ExchangeRate": {
                                "ForeignAsset": "u32",
                                "LendToken": "u32",
                                "LpToken": (
                                    {
                                        "ForeignAsset": "u32",
                                        "StableLpToken": "u32",
                                        "Token": "scale_info::51",
                                    },
                                    {
                                        "ForeignAsset": "u32",
                                        "StableLpToken": "u32",
                                        "Token": "scale_info::51",
                                    },
                                ),
                                "StableLpToken": "u32",
                                "Token": (
                                    "DOT",
                                    "IBTC",
                                    "INTR",
                                    "KSM",
                                    "KBTC",
                                    "KINT",
                                ),
                            },
                            "FeeEstimation": None,
                        },
                        "u128",
                    ),
                ],
            },
        )
