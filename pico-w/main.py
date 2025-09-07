import time
from audio_capture import AudioCapture
from motor_control import MotorController
from wifi_client import WiFiClient

class PicoWController:
    def __init__(self):
        self.audio = AudioCapture()
        self.motor = MotorController()
        self.wifi = WiFiClient()

    async def main_loop(self):
        while True:
            audio_data = self.audio.record()
            result = await self.wifi.send_audio_to_colab(audio_data)

            command = await self.wifi.send_audio_to_colab(audio_data)
            self.motor.execute_command(command)

            time.sleep(0.1)
