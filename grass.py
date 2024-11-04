import asyncio
import random
import ssl
import json
import time
import uuid
import os
from loguru import logger
import websockets
from fake_useragent import UserAgent

#### GET USER AGENT ####
useragent = UserAgent(os='windows', platforms='pc', browsers='chrome')
user_agent = useragent.random

# List of WebSocket URIs
ws_uris = [
    'wss://proxy2.wynd.network:4444/',
    'wss://proxy2.wynd.network:4650/'
]

async def send_ping(websocket):
    """Function to send PING messages at intervals."""
    while True:
        try:
            send_message = json.dumps({"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
            logger.debug(f"Sending PING: {send_message}")
            await websocket.send(send_message)
            await asyncio.sleep(5)  # Adjust this interval as needed
        except Exception as e:
            logger.error(f"Error in send_ping: {e}")
            break  # Exit if an error occurs

async def handle_messages(websocket, device_id, user_id, user_agent):
    """Function to handle incoming messages from the WebSocket."""
    while True:
        try:
            response = await websocket.recv()
            message = json.loads(response)
            logger.info(f"Received message: {message}")

            if message.get("action") == "AUTH":
                auth_response = {
                    "id": message["id"],
                    "origin_action": "AUTH",
                    "result": {
                        "browser_id": device_id,
                        "user_id": user_id,
                        "user_agent": user_agent,
                        "timestamp": int(time.time()),
                        "device_type": "extension",
                        "version": "4.26.2",
                        "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                    }
                }
                logger.debug(f"Sending AUTH response: {auth_response}")
                await websocket.send(json.dumps(auth_response))

            elif message.get("action") == "PONG":
                pong_response = {"id": message["id"], "origin_action": "PONG"}
                logger.debug(f"Sending PONG response: {pong_response}")
                await websocket.send(json.dumps(pong_response))

        except websockets.ConnectionClosed:
            logger.warning("WebSocket connection closed. Attempting to reconnect...")
            break  # Break to reconnect
        except Exception as e:
            logger.error(f"Error while receiving message: {e}")
            break  # Break to reconnect

async def connect_to_wss(user_id, uri):
    device_id = str(uuid.uuid4())
    logger.info(f"Connecting with Device ID: {device_id}")

    backoff_time = 1  # Initial backoff time in seconds
    while True:  # Main loop for connection attempts
        try:
            await asyncio.sleep(random.uniform(0.1, 1))  # Random delay before connecting
            custom_headers = {
                "User-Agent": user_agent,
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers) as websocket:
                logger.info("WebSocket connected")

                # Start sending PING messages
                asyncio.create_task(send_ping(websocket))
                
                # Handle incoming messages
                await handle_messages(websocket, device_id, user_id, custom_headers['User-Agent'])

        except Exception as e:
            logger.error(f"Connection error: {e}")
            logger.info(f"Retrying in {backoff_time} seconds...")
            await asyncio.sleep(backoff_time)
            backoff_time = min(backoff_time * 2, 30)  # Exponential backoff with a cap

async def main():
    user_id = '7ecb29fb-fadd-42e6-bac8-7f5daebf3413'
    
    # Randomly select a WebSocket URI
    selected_uri = random.choice(ws_uris)
    logger.info(f"Selected URI: {selected_uri}")

    await connect_to_wss(user_id, selected_uri)  # Await the connection function

if __name__ == '__main__':
    asyncio.run(main())