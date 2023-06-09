from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException


class ChainDEX(SubstrateInterface):
    def __init__(self):
        super().__init__(url="ws://localhost:8000")
        self.keypair = Keypair.create_from_uri("//Alice")

    def get_height(self) -> int:
        return self.get_block_number(self.get_chain_head())

    def exact_input_swap(
        self, amount_in: int, amount_out_min: int = 1, relative_deadline: int = 10
    ):

        call = self.compose_call(
            call_module="DexGeneral",
            call_function="swap_exact_assets_for_assets",
            call_params={
                "amount_in": amount_in,
                "amount_out_min": amount_out_min,
                "path": [{"Token": "KINT"}, {"Token": "KSM"}],
                "recipient": self.keypair.ss58_address,
                "deadline": (self.get_height() + relative_deadline),
            },
        )

        extrinsic = self.create_signed_extrinsic(call=call, keypair=self.keypair)

        try:
            receipt = self.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            print(
                f"Extrinsic '{receipt.extrinsic_hash}' sent and included in block '{receipt.block_hash}'"
            )

        except SubstrateRequestException as e:
            print("Failed to send: {}".format(e))
