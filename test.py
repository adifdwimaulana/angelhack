import os
import aiohttp
import asyncio
import dotenv
dotenv.load_dotenv()
PORT = os.getenv("PORT", 8000)
BASE_URL = f"http://localhost:{PORT}"


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
    sessionPostResponse = await session.post(f"{BASE_URL}/chat/{sessionId}", json={"message": "Hello!"})
    assert sessionPostResponse.status == 200
    sessionPostResponse = await sessionPostResponse.json()
    print(sessionPostResponse)

    # Be responsible and close the session
    await session.close()


if __name__ == "__main__":
    asyncio.run(test_chat_basic())
