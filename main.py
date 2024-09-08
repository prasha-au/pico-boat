import board
import busio
import digitalio
import asyncio
import pwmio
import neopixel


hull_light = pwmio.PWMOut(board.GP21)
hull_light.duty_cycle = 0

deck_light = neopixel.NeoPixel(board.GP23, 1)
deck_light[0] = (0, 0, 0)


motor_request = None
motor_left = pwmio.PWMOut(board.GP7)
motor_right = pwmio.PWMOut(board.GP8)

def set_motor_power(left, right):
  global motor_left, motor_right
  motor_left.duty_cycle = (65535 * left // 100)
  motor_right.duty_cycle = (65535 * right // 100)

set_motor_power(0, 0)

async def poll_motor_requests():
  global motor_request
  current_itr = 0
  while True:
    await asyncio.sleep(0.25)

    if motor_request != None:
      set_motor_power(motor_request[0], motor_request[1])
      motor_request = None
      current_itr = 0

    if current_itr < 10:
      current_itr += 1
    else:
      set_motor_power(0, 0)


uart = busio.UART(board.GP4, board.GP5, baudrate=9600, )

async def listen_for_commands():
  global motor_request, hull_light, deck_light

  uart.write("AT+DISC\r\n")
  uart.readline()
  uart.readline()

  uart.write("AT+NAMBBoaty\r\n")
  uart.readline()

  uart.write("AT+RESET\r\n")
  uart.readline()

  uart_rx = asyncio.StreamReader(uart)

  while True:
    data = await uart_rx.readline()
    print(f'Got request: {data}')

    str_data =  data.decode().rstrip()
    if str_data == 'forward':
      motor_request = (100, 100)
    elif str_data == 'left':
      motor_request = (0, 100)
    elif str_data == 'right':
      motor_request = (100, 0)
    elif str_data.startswith('hulllight'):
      if str_data.split('=')[1] == 'on':
        hull_light.duty_cycle = 65535
      else:
        hull_light.duty_cycle = 0
    elif str_data.startswith('decklight'):
      rgbstr = str_data.split('=')[1]
      deck_light[0] = [int(v) for v in rgbstr.split(',')]


async def main():
  asyncio.create_task(listen_for_commands())
  asyncio.create_task(poll_motor_requests())
  while True:
      await asyncio.sleep(10)

asyncio.run(main())

