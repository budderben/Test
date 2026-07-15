
import asyncio

async def send_hope_message(message):
  """Sends a message to the terminal every time the program opens."""
  print(message)

async def main():
  """The main function to run the message sending loop."""
  while True:
    await send_hope_message("The sun is shining bright, and so is hope!")  
# Replace with your message
    await asyncio.sleep(1)  # Pause for 1 second - adjust as needed


if __name__ == "__main__":
  asyncio.run(main())
