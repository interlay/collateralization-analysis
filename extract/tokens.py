import asyncio
from pprint import pprint
import ast
from substrateinterface import SubstrateInterface

from data.data_request import ToBaseDecimals


NATIVE_CURRENCIES = {
    "KINT": {"name": "Kintsugi", "symbol": "KINT", "decimals": 12},
    "KBTC": {"name": "Kintsugi Bitcoin", "symbol": "KBTC", "decimals": 8},
    "KSM": {"name": "Kusama", "symbol": "KSM", "decimals": 12},
    "INTR": {"name": "Interlay", "symbol": "INTR", "decimals": 10},
    "IBTC": {"name": "Interlay Bitcoin", "symbol": "IBTC", "decimals": 8},
    "DOT": {"name": "Polkadot", "symbol": "DOT", "decimals": 10},
}


from extract.coingecko import get_latest_coingecko_rates


def extract_substrate(
    substrate: SubstrateInterface,
    module: str,
    function: str,
    parameters: list = None,
    height: int = None,
):
    """
    Extract mapped data from a Substrate chain.

    Args:
      substrate (SubstrateInterface): The substrate interface to query.
      module (str): The module to query.
      function (str): The function to query.
      parameters (list): The parameters to pass to the function.
      height (int): The height of the block to query.

    Returns:
      dict: The response data with at most 1000 entries.
    """
    max_results = 100000
    page_size = 200

    block_hash = None
    if height is not None:
        block_hash = substrate.get_block_hash(height)

    try:
        response = substrate.query_map(
            module,
            function,
            parameters,
            block_hash,
            page_size=page_size,
            max_results=max_results,
        )
    except BaseException as e:
        print(
            "Failed to query map {}.{}({}): {} at height {}".format(
                module, function, parameters, e, height
            )
        )
        try:
            storage_function = substrate.get_metadata_storage_function(module, function)
            print(
                "Tip: The function expects a parameter from \n {}.".format(
                    storage_function.get_param_info()
                )
            )
        except BaseException:
            pass
        return {}

    # Construct a dict from the response.
    data = {}
    for key, values in response:
        # print("Key {}".format(key))
        # print("Values {}".format(values.value))
        derived_key = "{}".format(key)
        # This deconstructs the key if it is a dict and stores it as a nested dict.
        # Currencies are stored in this way:
        # {
        #  { "Token": "DOT" },
        #  { "ForeignAsset": 1}
        # }
        try:
            maybe_dict_key = ast.literal_eval(derived_key)
        except BaseException:
            maybe_dict_key = None
        if isinstance(maybe_dict_key, dict):
            main_key, nested_key = next(iter(maybe_dict_key.items()))

            nested_derived_key = "{}".format(nested_key)

            try:
                data[main_key][nested_derived_key] = values.value
            except KeyError:
                # Handle the case where the main key does not exist.
                value = {nested_derived_key: values.value}
                data[main_key] = value
        else:
            data[derived_key] = values.value
    return data


async def extract_onchain_tokens(substrate, height=None):
    """
    Get all assets on the chain.
    """
    tokens = await asyncio.gather(
        extract_native_tokens(substrate, height),
        extract_foreign_tokens(substrate, height),
        extract_dex_tokens(substrate, height),
        extract_lending_tokens(substrate, height),
    )

    return {**tokens[0], **tokens[1], **tokens[2][0], **tokens[2][1], **tokens[3]}


async def extract_native_tokens(substrate, height=None):
    """
    Get all native assets on the chain.
    """
    return {"Token": NATIVE_CURRENCIES}


async def extract_foreign_tokens(substrate, height=None):
    """
    Get all foreign assets on the chain.
    """
    foreign_tokens = await extract_substrate(
        substrate, "AssetRegistry", "Metadata", height
    )
    foreign_tokens = {int(k): v for k, v in foreign_tokens.items()}

    return {"ForeignAsset": foreign_tokens}


async def extract_lending_tokens(substrate, height=None):
    """
    Map all lending tokens on the chain to their assets.
    """

    markets = await extract_substrate(substrate, "Loans", "Markets", height)

    tokens = {}
    for token_type, market in markets.items():
        for token, market_conf in market.items():
            if token_type == "ForeignAsset":
                # convert foreign assets to their integer id
                token = int(token)
            tokens[market_conf["lend_token_id"]["LendToken"]] = {token_type: token}

    return {"LendToken": tokens}


async def extract_dex_tokens(substrate, height=None):
    """
    Map all dex tokens on the chain to their assets.
    """

    [xyk_pools, stable_pools] = await asyncio.gather(
        extract_substrate(substrate, "DexGeneral", "LiquidityPairs", height),
        extract_substrate(substrate, "DexStable", "Pools", height),
    )

    xyk_lp_tokens = {token: conf["LpToken"] for token, conf in xyk_pools.items()}

    stable_lp_tokens = {}
    for token, conf in stable_pools.items():
        if "Base" in conf:
            # Base pools consists of two or more currencies stored in an array
            stable_lp_tokens[int(token)] = conf["Base"]["currency_ids"]
        elif "Meta" in conf:
            # Meta pools consist of a base pool and an additional currency
            stable_lp_tokens[int(token)] = conf["Meta"]["info"]["currency_ids"]

    lp_tokens = [{"LpToken": xyk_lp_tokens}, {"StableLpToken": stable_lp_tokens}]

    return lp_tokens


async def extract_and_map_exchange_rates_to_tokens(substrate, height=None):
    """
    Get the on-chain tokens.
    Get the internal exchange rates the dex and lending tokens from the chain.
    Get the exchange rates for the native and foreign assets from coingecko: try the warehouse first and if this fails use the API.

    Map the exchange rates to the tokens.

    Returns:
        A dict of exchange rates to USD and their timestamp.
    """

    # loans.exchangeRates to get qtoken rates
    [tokens, lending_rates, dex_token_weights] = await asyncio.gather(
        extract_onchain_tokens(substrate, height),
        extract_substrate(substrate, "Loans", "ExchangeRate", height),
        extract_dex_token_weights(substrate, height),
    )

    exchange_rates = await extract_exchange_rates(tokens)

    return map_exchange_rates_to_tokens(
        tokens, exchange_rates, lending_rates, dex_token_weights
    )


async def extract_exchange_rates(tokens):
    """
    Get the exchange rates from coingecko for the Token and ForeignAssets.

    Args:
      tokens: A dict of on-chain tokens to get the exchange rates for.

    Returns:
      A dict of exchange rates to USD and their timestamp.
    """
    # The base tokens are used to compose dex and lending tokens
    token_symbols = list(tokens["Token"].keys())
    for symbol in tokens["ForeignAsset"].values():
        token_symbols.append(symbol["symbol"])

    coingecko_rates = await get_latest_coingecko_rates(token_symbols)
    return coingecko_rates


def map_exchange_rates_to_tokens(
    tokens, exchange_rates, lending_rates, dex_token_weights
):
    """
    Map the exchange rates to the tokens.
    """

    # Transform foreign asset keys to int
    if "ForeignAsset" in lending_rates:
        lending_rates["ForeignAsset"] = {
            int(k): v for k, v in lending_rates["ForeignAsset"].items()
        }
    pprint(exchange_rates)

    # Add usd prices to tokens and foreign assets
    for token, conf in tokens["Token"].items():
        symbol = token
        rate = exchange_rates[symbol]["usdRate"] / 10 ** conf["decimals"]
        tokens["Token"][token]["usdRate"] = rate

    for token, conf in tokens["ForeignAsset"].items():
        symbol = conf["symbol"]
        rate = exchange_rates[symbol]["usdRate"] / 10 ** conf["decimals"]
        tokens["ForeignAsset"][token]["usdRate"] = rate

    # Lending tokens need to be mapped to their foreign asset and tokens
    for token, conf in tokens["LendToken"].items():
        lending_token_type, lending_token = next(iter(conf.items()))
        if lending_token_type == "Token":
            symbol = lending_token
        elif lending_token_type == "ForeignAsset":
            symbol = tokens[lending_token_type][lending_token]["symbol"]
        rate = (
            lending_rates[lending_token_type][lending_token]
            / ToBaseDecimals.PERCENTAGE.get_decimals()
            * tokens[lending_token_type][lending_token]["usdRate"]
        )
        tokens["LendToken"][token]["usdRate"] = rate

    for token, pairs in tokens["LpToken"].items():
        usd_value = []
        # Pairs is a tuple like ({"Token": "DOT"}, {"Token": "KSM"})
        for pair in pairs:
            for token_type, identifier in pair.items():
                weight = dex_token_weights["LpToken"][token][token_type][identifier]
                usd_value.append(weight * tokens[token_type][identifier]["usdRate"])
        # move the token tuple to a dict
        tokens["LpToken"][token] = {"Tokens": pairs, "usdRate": sum(usd_value)}

    # Flatten nested stable pairs
    for token, pairs in tokens["StableLpToken"].items():
        # Pairs is a list of dicts like [{"Token": "DOT"}, {"Token": "KSM"}]
        flattened_pairs = []
        for pair in pairs:
            for token_type, identifier in pair.items():
                if token_type == "StableLpToken":
                    flattened_pairs.extend(tokens["StableLpToken"][identifier])
                else:
                    flattened_pairs.append({token_type: identifier})
        tokens["StableLpToken"][token] = flattened_pairs

    for token, pairs in tokens["StableLpToken"].items():
        usd_value = []
        for pair in pairs:
            for token_type, identifier in pair.items():
                weight = dex_token_weights["StableLpToken"][token][token_type][
                    identifier
                ]
                usd_value.append(weight * tokens[token_type][identifier]["usdRate"])
        # move the token list to a dict
        tokens["StableLpToken"][token] = {"Tokens": pairs, "usdRate": sum(usd_value)}
    pprint(tokens)
    return tokens


async def extract_dex_token_weights(substrate, height=None):
    """
    Get the weights for the dex tokens.

    Args:
      tokens: A dict of tokens to get the weights for.

    Returns:
      A dict of dex token weights.
    """
    [general_pair_weights, stable_pair_weights] = await asyncio.gather(
        extract_dex_general_tokens_weights(substrate, height),
        extract_dex_stable_tokens_weights(substrate, height),
    )

    return {
        "LpToken": general_pair_weights,
        "StableLpToken": stable_pair_weights,
    }


async def extract_dex_general_tokens_weights(substrate, height=None):
    """
    Get the weights for the dex general tokens.

    Returns:
      A dict of dex general token weights.
    """
    from extract.users import extract_user_portfolios

    pair_status = await extract_substrate(
        substrate, "DexGeneral", "PairStatuses", height
    )

    # Get all the pair accounts that store the tokens in the pool
    pair_accounts = {}
    for token_pair, config in pair_status.items():
        pair_accounts[token_pair] = config["Trading"]["pair_account"]

    pair_tokens = await extract_user_portfolios(substrate, pair_accounts.values())

    return calculate_dex_general_token_weights(pair_status, pair_tokens)


def calculate_dex_general_token_weights(pair_status, pair_tokens):
    """
    Determine the pair weights for each pair
    token_1_weight = token_1_amount / total_supply
    token_2_weight = token_2_amount / total_supply
    token_3_weight = token_3_amount / total_supply
    ...
    """
    import ast

    pair_weights = {}
    for token_pair, config in pair_status.items():
        total_supply = config["Trading"]["total_supply"]
        account = config["Trading"]["pair_account"]
        tokens = ast.literal_eval(token_pair)
        weights = {}
        # Tokens is a set
        for pair in tokens:
            for token, identifier in pair.items():
                if token not in weights:
                    weights[token] = {}

                weights[token][identifier] = (
                    pair_tokens[account][token][identifier] / total_supply
                )
        pair_weights[token_pair] = weights

    return pair_weights


async def extract_dex_stable_tokens_weights(substrate, height=None):
    """
    Get the weights for the dex stable tokens.

    Returns:
      A dict of dex stable token weights.
    """
    [total_issuance, stable_pools] = await asyncio.gather(
        extract_substrate(substrate, "Tokens", "TotalIssuance", height),
        extract_substrate(substrate, "DexStable", "Pools", height),
    )

    if len(stable_pools) == 0:
        return {}

    stable_lp_issuance = {
        (int(k)): v for k, v in total_issuance["StableLpToken"].items()
    }

    return compute_dex_stable_token_weights(stable_lp_issuance, stable_pools)


def compute_dex_stable_token_weights(stable_lp_issuance, stable_pools):
    """
    Get the weights for the dex stable tokens.
    """

    # Process base pools before meta pools so we can flatten it
    stable_pools_sorted = []
    for stable_lp, pool in stable_pools.items():
        if "Meta" in pool:
            stable_pools_sorted.append((stable_lp, pool))
        else:
            stable_pools_sorted.insert(0, (stable_lp, pool))

    pair_weights = {}
    for stable_lp, pool in stable_pools_sorted:
        total_issuance = stable_lp_issuance[int(stable_lp)]
        weights = {}
        if "Meta" in pool:
            tokens = pool["Meta"]["info"]["currency_ids"]
            balances = pool["Meta"]["info"]["balances"]

        else:
            tokens = pool["Base"]["currency_ids"]
            balances = pool["Base"]["balances"]

        for i in range(len(tokens)):
            [name, identifier] = next(iter(tokens[i].items()))

            # Flatten nested stable tokens
            if name == "StableLpToken":
                base_pool_weights = pair_weights[identifier]
                for base_name, base_token in base_pool_weights.items():
                    for base_identifier, base_weight in base_token.items():
                        if base_name not in weights:
                            weights[base_name] = {}

                        weights[base_name][base_identifier] = base_weight * (
                            balances[i] / total_issuance
                        )
            else:
                if name not in weights:
                    weights[name] = {}
                weights[name][identifier] = balances[i] / total_issuance
            pair_weights[int(stable_lp)] = weights

    return pair_weights
