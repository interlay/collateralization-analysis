#%%
from chopsticks.state_queries import Kintsugi
from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

kintsugi = SubstrateInterface(url="ws://localhost:8000")

# %%
for k, v in kintsugi.vault_thresholds.items():
    print(k)
    for collateral, threshold in v:
        print(f"{collateral} is: {threshold.value/1e16}%")
#%%
oracles = kintsugi.get_authorized_oracles()
for k, v in oracles:
    print(k, v)
# %%
keypair = Keypair.create_from_uri("//Alice")
call = kintsugi.compose_call(
    call_module="Oracle",
    call_function="remove_authorized_oracle",
    call_params={"account_id": "14ysUis7oxFQ3JHemZ8pnaBbQfm4SXt5E21J1xT6nx3A5ysB"},
)
# %%
batched_call = kintsugi.compose_call(
    call_module="Utility", call_function="batch", call_params={"calls": [call]}
)

sudo_call = kintsugi.compose_call("Sudo", "sudo", {"call": batched_call})

# %%
extrinsic = kintsugi.create_signed_extrinsic(call=sudo_call, keypair=keypair)
# %%
try:
    receipt = kintsugi.submit_extrinsic(extrinsic, wait_for_inclusion=True)

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

# %%
oracles = kintsugi.query_map(module="Oracle", storage_function="AuthorizedOracles")
for k, v in oracles:
    print(k, v)
# %%
