import aiohttp
import asyncio


async def _fetch_async(session, url):
    """
    Given an aiohttp.ClientSession and a URL,
    return a Future to resolve a response dictionary of the form:

    {'text': TEXT_CONTENT, 'response': aiohttp.ClientResponse}
    """

    async with session.get(url) as response:
        response.raise_for_status()

        text = await response.text()

        return {"text": text, "response": response}


async def _fetch_concurrently(urls):
    """
    Use an aiohttp.ClientSession to run _fetch_async
    against each URL in a list, and gather all the
    responses together in a Future
    """

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5)
    ) as session:
        queue = []

        for url in urls:
            queue.append(_fetch_async(session, url))

        return await asyncio.gather(*queue)


def fetch_all(urls):
    """
    Fetch all the URLs and return their responses as a list,
    in the form:

    [
        {'text': TEXT_CONTENT, 'response': aiohttp.ClientResponse},
        ...
    ]
    """

    loop = asyncio.new_event_loop()
    return loop.run_until_complete(_fetch_concurrently(urls))
