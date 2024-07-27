import os
import aiohttp
import asyncio
import dotenv

dotenv.load_dotenv()
PORT = os.getenv("PORT", 8000)
BASE_URL = f"http://localhost:{PORT}"


async def wait_for_server():
    while True:
        try:
            print("Checking if server is running...")
            async with aiohttp.ClientSession() as session:
                async with session.get(BASE_URL) as response:
                    return
        except aiohttp.client_exceptions.ClientConnectorError:
            await asyncio.sleep(1)
            print("Waiting for server to start...")


async def test_chat_basic():
    session = aiohttp.ClientSession()

    # POST /chat
    sessionPostResponse = await session.post(f"{BASE_URL}/chat")
    sessionId = await sessionPostResponse.json()
    sessionId = sessionId["session_id"]

    assert sessionPostResponse.status == 200
    assert sessionId != None

    # GET /chat/{sessionId}
    sessionGetResponse = await session.get(f"{BASE_URL}/chat/{sessionId}")
    assert sessionGetResponse.status == 200
    sessionGetResponse = await sessionGetResponse.json()
    assert sessionGetResponse == []

    # POST /chat/{sessionId}
    sessionPostResponse = await session.post(f"{BASE_URL}/chat/{sessionId}", json={"message": ""})
    assert sessionPostResponse.status == 200
    sessionPostResponse = await sessionPostResponse.json()
    print(sessionPostResponse)

    # POST /chat/{sessionId}
    sessionPostResponse = await session.post(f"{BASE_URL}/chat/{sessionId}", json={"message": "Yang manis"})
    assert sessionPostResponse.status == 200
    sessionPostResponse = await sessionPostResponse.json()
    print(sessionPostResponse)

    # Be responsible and close the session
    await session.close()


async def test_order_plan():
    session = aiohttp.ClientSession()

    # POST /order/plan
    sessionPostResponse = await session.post(f"{BASE_URL}/order/plan", json={"messages": ""})
    sessionPostResponseJson = await sessionPostResponse.json()
    assert sessionPostResponse.status == 200
    print(sessionPostResponseJson)

    # Be responsible and close the session
    await session.close()


async def main():
    await wait_for_server()
    await asyncio.gather(test_chat_basic(), test_order_plan())


if __name__ == "__main__":
    asyncio.run(main())
