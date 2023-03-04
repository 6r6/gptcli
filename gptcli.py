#!/usr/bin/env python3

import os
import asyncio
import argparse
import openai
import re

from rich.console import Console
from rich.markdown import Markdown, MarkdownIt
from rich.live import Live
from aiohttp import ClientSession

c = Console()
sep = Markdown("---")
baseDir = os.path.dirname(os.path.realpath(__file__))
systemPrompt = { "role": "system", "content": "Use triple backticks with the language name for every code block in your markdown response, if any." }

class Config:
    aio_socks_proxy = None

def query_openai(data: dict):
    messages = [ systemPrompt ]
    messages.extend(data)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    content = response["choices"][0]["message"]["content"]
    c.print(Markdown(content), sep)
    return content

def query_openai_bypass(data: dict):
    messages = [ systemPrompt ]
    messages.extend(data)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    content = response["choices"][0]["message"]["content"]

    # calculate english words and chinese words, 
    # one chinese word is counted as two english words
    englishwords = len(re.findall(r'\b\w+\b', content))
    chineseWords = sum(1 for ch in content if '\u4e00' <= ch <= '\u9fff')
    wordCount = englishwords + chineseWords*2

    temperature = 1.5
    frequencyPenalty = 1.0

    extraParamsDict = {
        (0, 250): (1.7, 2.0),
        (251, 500): (1.5, 1.2),
        (501, 750): (1.2, 0.6),
        (751, 1000): (1.1, 0.5),
        (1001, 4096): (1.0, 0.4),
        (4097, float('inf')): (1.0, 1.0)
    }

    for wordRange, values in extraParamsDict.items():
        if wordRange[0] < wordCount <= wordRange[1]:
            temperature, frequencyPenalty = values
            maxTokens = wordRange[1]
            break
    
    c.print(f"[Bypass Parameters]\n \
            initial_responsed_words: {wordCount} --> max_tokens: {maxTokens}, \
            temperature: {temperature}, frequencyPenalty: {frequencyPenalty}\n")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=maxTokens,
        temperature=temperature,
        top_p=1,
        frequency_penalty=frequencyPenalty,
        presence_penalty=0
    )
    content = response["choices"][0]["message"]["content"]
    c.print(Markdown(content), sep)
    return content

async def query_openai_stream(data: dict):
    messages = [ systemPrompt ]
    messages.extend(data)
    md = Markdown("")
    parser = MarkdownIt().enable("strikethrough")
    if Config.aio_socks_proxy:
        try:
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(Config.aio_socks_proxy)
            openai.aiosession.set(ClientSession(connector=connector))
        except ImportError:
            c.print("aiohttp_socks not installed, socks proxy for aiohttp won't work")
            Config.aio_socks_proxy = None
    with Live(md, auto_refresh=False) as lv:
        async for part in await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        ):
            finish_reason = part["choices"][0]["finish_reason"]
            if "content" in part["choices"][0]["delta"]:
                content = part["choices"][0]["delta"]["content"]
                md.markup += content
                md.parsed = parser.parse(md.markup)
                lv.refresh()
            elif finish_reason:
                pass
    c.print(sep)
    if Config.aio_socks_proxy:
        await openai.aiosession.get().close()
    return md.markup


def print_help():
    c.print("""options:
  <        input multiline, end with ctrl-d(Linux/macOS) or ctrl-z(Windows)
  reset    reset session, i.e. clear chat history
  help     show this help message
  exit     exit console
""")

def setup_readline():
    def completer(text, state):
        options = ['reset', 'help', 'exit', '<<<']
        matches = [o for o in options if o.startswith(text)]
        if state < len(matches):
            return matches[state]
        else:
            return None
    readline.set_completer(completer)
    readline.parse_and_bind('tab:complete')

def read_multiline() -> str:
    contents = []
    c.print("Input multiline data, cancel with ctrl-c:")
    while True:
        try:
            line = input()
        except EOFError:
            c.print("--- EOF ---")
            break
        except KeyboardInterrupt:
            return ""
        contents.append(line)
    return "\n".join(contents)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", dest="no_stream", action="store_true", help="query openai in non-stream mode")
    parser.add_argument("-r", dest="response", action="store_true",
                        help="attach server response in request prompt, consume more tokens to get better results")
    parser.add_argument("-k", dest="key", help="path to api_key", default=os.path.join(baseDir, ".key"))
    parser.add_argument("-p", dest="proxy", help="http/https proxy to use")
    parser.add_argument("-b", dest="bypass_detector", action="store_true", help="bypass the ai detector in no_stream mode")
    args = parser.parse_args()

    try:
        import readline
        setup_readline()
    except Exception:
        pass

    c.print(f"Loading key from {args.key}")
    with open(args.key, "r") as f:
        openai.api_key = f.read().strip()
    stream = not args.no_stream
    if args.proxy:
        c.print(f"Using proxy: {args.proxy}")
        if stream and args.proxy.startswith("socks"):
            Config.aio_socks_proxy = args.proxy
        else:
            openai.proxy = args.proxy
    c.print(f"Attach response in prompt: {args.response}")
    if args.bypass_detector:
        stream = not stream
        c.print(f"Bypassing ai detector: True")
    c.print(f"Stream mode: {stream}")

    data = []
    while True:
        try:
            # content = c.input("[bold yellow]Input:[/] ").strip()
            with c.capture() as capture:
                c.print("[bold yellow]Input:[/] ", end="")
            content = input(capture.get())
            if content == "<":
                content = read_multiline()
            content = content.strip()
            if not content:
                continue
            if content == "reset":
                data.clear()
                c.print("Session reset.")
                continue
            if content == "help":
                print_help()
                continue
            if content == "exit":
                break
            data.append({"role": "user", "content": content})
            if stream:
                answer = asyncio.run(query_openai_stream(data))
            elif args.bypass_detector:
                answer = query_openai_bypass(data)
            else:
                answer = query_openai(data)
        except openai.error.RateLimitError as e:
            c.print(e)
            continue
        except KeyboardInterrupt:
            c.print("Bye!")
            break
        except EOFError as e:
            c.print("Bye!")
            break
        if args.response:
            data.append({"role": "assistant", "content": answer})
