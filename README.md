# Chapter 1: set up an endpoint

Branch `ch1-endpoint`. Before: `ch0-setup`. Next: `ch2.1-sandbox`.

The agent will need a model. You make a proxy token for your Environment, a
Model Endpoint for Kimi K3, billed per token, and a Secret that holds the
token. The code gains one line: `MODEL`, read from `ENDPOINT_URL`.

## Set up, in this order

```sh
modal workspace proxy-tokens create --name vibecoding-demo     # prints wk-… and ws-…, once
modal workspace proxy-tokens allow wk-… <your Environment>
export AUTHORIZATION_BEARER=wk-….ws-…                          # the id, a dot, the secret
modal endpoint create --shared --model moonshotai/Kimi-K3 --name kimi-k3
modal secret create model-token AUTHORIZATION_BEARER=$AUTHORIZATION_BEARER
export ENDPOINT_URL=$(modal endpoint info kimi-k3 --json | jq -r .service_url)
```

- **Let the token into the Environment before you create the Endpoint.** The
  other order fails with `Create a proxy token to require authentication…`.
- **Every terminal needs `ENDPOINT_URL` from here on.** Without it the code
  stops with `KeyError: 'ENDPOINT_URL'`. Without `jq`, copy the URL by hand.

## Run it

```sh
curl $ENDPOINT_URL/v1/chat/completions \
  -H "Authorization: Bearer $AUTHORIZATION_BEARER" \
  -d '{"messages": [{"role": "user", "content": "Say hello in one word"}]}'
curl $ENDPOINT_URL/v1/chat/completions \
  -d '{"messages": [{"role": "user", "content": "Say hello in one word"}]}'
```

With the token, the model answers in JSON, with `"model":"moonshotai/Kimi-K3"`.
Without it, the answer is `{"error":"proxy auth required"}`.

## Test it

```sh
uv run checks/ch1_endpoint.py     # from the repository root
```

Done when the first call answers 200 and the second 401.

## See what changed

```sh
git diff ch0-setup ch1-endpoint -- code
```
