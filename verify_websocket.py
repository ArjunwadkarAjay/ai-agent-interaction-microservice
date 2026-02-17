import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/chat"
    payload = {
        "message": "Count from 1 to 5.",
        "model": "hf.co/liquidai/lfm2.5-1.2b-instruct-gguf:Q4_K_M",
        "temperature": 0.5,
        "stream": True # Ignored by WS but good to conform to schema
    }
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected. Sending payload...")
            await websocket.send(json.dumps(payload))
            
            print("Receiving messages...")
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "content" in data:
                        print(f"Token: {data['content']}", end="", flush=True)
                    elif "metadata" in data:
                        print(f"\n\nMetadata received: {json.dumps(data['metadata'], indent=2)}")
                        break
                    elif "error" in data:
                        print(f"\nError: {data['error']}")
                        break
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server.")
                    break
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
