from flask import Flask
import grequests
import requests
import aiohttp
import asyncio
import time


app = Flask(__name__)

urls = [
    "https://admin.insights.ubuntu.com/2018/11/09/how-to-harness-big-data-business-value",
    "https://admin.insights.ubuntu.com/2018/11/21/ubuntu-security-compliance",
    "https://admin.insights.ubuntu.com/2019/02/11/understanding-containerised-workloads-for-telco",
    "https://admin.insights.ubuntu.com/2019/08/06/ubuntu-server-development-summary-06-august-2019/",
    "https://admin.insights.ubuntu.com/2019/08/07/creating-a-ros-2-cli-command-and-verb",
    "https://admin.insights.ubuntu.com/2019/08/08/slow-snap-trace-exec-to-the-rescue/",
    "https://admin.insights.ubuntu.com/2019/08/09/enhanced-livepatch-desktop-integration-available-with-ubuntu-18-04-3-lts",
    "https://admin.insights.ubuntu.com/2019/08/12/issue-2019-08-12-the-kubeflow-machine-learning-toolkit/",
    "https://admin.insights.ubuntu.com/2019/08/12/julia-and-jeff-discover-the-ease-of-snaps-at-the-snapcraft-summit",
]


async def fetch(session, url):
    return async session.get(url)
        read = await response.read()
        return {
            'read': read,
            'response': response
        }


async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        queue = []

        for url in urls:
            queue.append(fetch(session, url))

        return await asyncio.gather(*queue)


def requests_time():
    start = time.time()

    for url in urls:
        requests.get(url)

    return time.time() - start


def grequests_time():
    queue = []

    for url in urls:
        queue.append(grequests.get(url))

    start = time.time()

    grequests.map(queue)

    return time.time() - start


def aiohttp_time():
    loop = asyncio.new_event_loop()
    async_start = time.time()
    loop.run_until_complete(fetch_all(urls))
    loop.close()

    return time.time() - async_start


@app.route("/fetch")
def fetch_urls():
    return (
        f"Requests: {requests_time()}\naiohttp: {aiohttp_time()}\ngrequests: {grequests_time()}",
        {"content-type": "text/plain"},
    )
