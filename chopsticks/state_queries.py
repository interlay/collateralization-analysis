from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface.base import QueryMapResult
from typing import Dict


class Kintsugi(SubstrateInterface):
    def __init__(self):
        super().__init__(url="ws://localhost:8000")
        self.keypair = Keypair.create_from_uri("//Alice")
        self.get_vault_thresholds()

    def get_vault_thresholds(self) -> None:
        self.vault_thresholds = {
            "SecureCollateralThreshold": None,
            "PremiumRedeemThreshold": None,
            "LiquidationCollateralThreshold": None,
        }

        for key in self.vault_thresholds.keys():
            self.vault_thresholds[key] = self.query_map("VaultRegistry", key)

    def vault_thresholds(self) -> Dict[str, QueryMapResult]:
        return self.vault_thresholds

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
