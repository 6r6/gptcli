Take chatGPT into command line.

[![stream](./stream.svg)][vid]

# Setup

1. clone this repo
2. pip3 install -U -r requirements.txt
3. get your apikey from <https://platform.openai.com/account/api-keys> and put it in `.key`

# Run

```sh
$ ./gptcli.py -h
usage: gptcli.py [-h] [-r] [-k KEY] [-p PROXY]

options:
  -h, --help  show this help message and exit
  -n          query openai in non-stream mode (default: False)
  -r          attach server response in request prompt, consume more tokens to get better results (default: False)
  -k KEY      path to api_key (default: .key)
  -p PROXY    http/https proxy to use (default: None)
```

Console help:

```
$ gptcli.py -rp socks5://localhost:1080
Loading key from .key
Using proxy: socks5://localhost:1080
Attach response in prompt: True
Stream mode: True
Input: help
options:
  <        input multiline, end with ctrl-d(Linux/macOS) or ctrl-z(Windows)
  reset    reset session, i.e. clear chat history
  help     show this help message
  exit     exit console
```

# Run in Docker

```sh
docker build -t gptcli:latest .
# Change path_to_key_on_the_host to the path where your .key file is stored on the host.
docker run -it --rm -v ~/path_to_key_on_the_host/gptcli.key:/gptcli/.key gptcli:latest
# Run in bypass ai detector mode
docker run -it --rm -v ~/path_to_key_on_the_host/gptcli.key:/gptcli/.key gptcli:latest -b
```

# Example

![demo](./demo.jpg)

# Feature

- [x] Session based
- [x] Markdown support
- [x] Syntax highlight
- [x] Proxy support
- [x] Multiline input
- [x] Stream output


> NOTE: openai's library use aiohttp for stream mode request, and `aiohttp` only supports http/https proxy, not socks5.
> see: https://github.com/aio-libs/aiohttp/pull/2539
> The workaround is to use `aiohttp_socks` module for socks proxy in stream mode


# LINK

- https://platform.openai.com/docs/introduction
- https://platform.openai.com/docs/api-reference/completions
- https://platform.openai.com/account/api-keys

[vid]: https://asciinema.org/a/564585
