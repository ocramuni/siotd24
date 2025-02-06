import RPi.GPIO as GPIO

class Led:
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def on(self) -> str:
        GPIO.output(self.pin, GPIO.HIGH)
        return 'LED on'

    def off(self) -> str:
        GPIO.output(self.pin, GPIO.LOW)
        return 'LED off'

    def status(self) -> str:
        state = GPIO.input(self.pin)
        if state == GPIO.HIGH:
            text = 'LED on'
        else:
            text = 'LED off'
        return text

    def shutdown(self) -> None:
        GPIO.cleanup()