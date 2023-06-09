import ast
import requests


async def extract_graphql(endpoint, query, timeout=1):
    """
    Extract data from a GraphQL endpoint.

    Args:
      endpoint (str): The endpoint to query.
      query (str): The graphql query to execute.
      timeout (int): The timeout in seconds. Default to 1 second.

    Returns:
      dict: The response data.
    """
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        endpoint, json={"query": query}, headers=headers, timeout=timeout
    )
    data = response.json()["data"]
    return data


async def extract_substrate(substrate, module, function, parameters=None, height=None):
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
    # print("Returning at most {} results.".format(max_results))

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


async def extract_substrate_rpc(substrate, method, params=None):
    """
    Extract data from a Substrate RPC endpoint.

    Args:
      substrate (SubstrateInterface): The substrate interface to query.
      method (str): The method to query.
      params (list): The parameters to pass to the method.

    Returns:
      dict: The response data.
    """
    response = substrate.rpc_request(method, params)
    data = response
    return data


async def extract_coingecko(query, args=None):
    """
    Extract data from the coingecko API.

    Args:
      query (str): The query to execute.
      args (list): The arguments to pass to the query.

    Returns:
      dict: The response data.
    """
    endpoint = "https://api.coingecko.com/api/v3/{}?{}".format(query, args)
    response = requests.get(endpoint, params=args)
    data = response.json()
    return data
