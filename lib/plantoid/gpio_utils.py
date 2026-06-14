"""
Non-blocking GPIO Controller for Plantoid 
Runs LED animation in a separate thread
"""
import RPi.GPIO as GPIO
import os
import time
import board
import neopixel
#import digitalio
import random
import threading

class GPIOLEDController:
    """Non-blocking LED controller that runs animations in a background thread"""
    
    def __init__(self, led_pin=board.D10, led_count=16, brightness=0.5):
        
        if led_pin not in [18, 21]:
            print(f"Warning: For stable NeoPixel output, it's highly recommended to use GPIO 18 or 21 (you are using {led_pin}).")
        
        self.led_pin = getattr(board, f'D{led_pin}') 
        self.led_count = led_count
        self.brightness = brightness
        
        # Create NeoPixel object
        self.pixels = neopixel.NeoPixel(
            self.led_pin, 
            self.led_count, 
            brightness=self.brightness, 
            auto_write=False
        )
        
        # Thread control
        self.current_state = "asleep"
        self.running = True
        self.animation_thread = None
        
        # Start animation thread
        self.start_animation_thread()
    
    def start_animation_thread(self):
        """Start the background animation thread"""
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
    
    def set_state(self, state):
        """
        Set the LED state (non-blocking)
        States: 'awake', 'asleep', 'listening', 'thinking', 'speaking'
        """
        state = state.lower().strip('<>')
        if state in ['awake', 'asleep', 'listening', 'thinking', 'speaking']:
            if self.current_state != state: # only change if needed     
                self.current_state = state
                print(f"LED state changed to: {state}")
        else:
            print(f"Warning: Unknown LED state '{state}'")
    
    def _animation_loop(self):
        """Main animation loop (runs in separate thread)"""
        while self.running:
            try:
                if self.current_state == "asleep":
                    self._asleep_animation()
                elif self.current_state == "awake":
                    self._awake_animation()
                elif self.current_state == "listening":
                    self._listening_animation()
                elif self.current_state == "thinking":
                    #self._thinking_animation()
                    self._theater_chase_animation()
                elif self.current_state == "speaking":
                    self._speaking_animation()
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Animation error: {type(e).__name__}: {e!r}")
                time.sleep(0.5)
    
    def _asleep_animation(self):
        """Green breathing - asleep/idle state"""
        initial_state = self.current_state

        for i in range(40):
            if self.current_state != initial_state:
                return
            # Calculate brightness 0.0 to 1.0
            brightness = abs((i % 40) - 20) / 20.0
            # Convert to 0-255 range
            g = int(brightness * 255)
            color = (0, g, 0)  # Green
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(0.05)
    
    def _awake_animation(self):
        """Cyan breathing - awake/ready state"""
        initial_state = self.current_state

        for i in range(40):
            if self.current_state != initial_state:
                return
            # Calculate brightness 0.0 to 1.0
            brightness = abs((i % 40) - 20) / 20.0
            # Convert to 0-255 range
            g = int(brightness * 255)
            b = int(brightness * 255)
            color = (0, g, b)  # Cyan
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(0.05)
    
    def _listening_animation(self):
        """Fire flickering effect - listening state"""
        initial_state = self.current_state

        for _ in range(30):
            if self.current_state != initial_state:
                return
            for i in range(self.led_count):
                flicker = random.randint(100, 255)
                self.pixels[i] = (flicker, flicker // 3, 0)
            self.pixels.show()
            time.sleep(0.033)
    
    def _thinking_animation(self):
        initial_state = self.current_state

        """Police strobe - thinking/processing state"""
        for _ in range(8):
            if self.current_state != initial_state:
                return
            # Red flash
            self.pixels.fill((255, 0, 0))
            self.pixels.show()
            time.sleep(0.08)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            time.sleep(0.08)
            # Blue flash
            self.pixels.fill((0, 0, 255))
            self.pixels.show()
            time.sleep(0.08)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            time.sleep(0.08)
    
    def _speaking_animation(self):
        initial_state = self.current_state

        """Red scanner/larson - speaking state"""
        # Forward scan
        for i in range(self.led_count):
            if self.current_state != initial_state:
                return
            self.pixels.fill((0, 0, 0))
            self.pixels[i] = (255, 0, 0)  # Red
            if i > 0:
                self.pixels[i-1] = (100, 0, 0)  # Trail
            if i > 1:
                self.pixels[i-2] = (30, 0, 0)  # Fade
            self.pixels.show()
            time.sleep(0.03)
        
        # Backward scan
        for i in range(self.led_count - 1, -1, -1):
            if self.current_state != "speaking":
                return
            self.pixels.fill((0, 0, 0))
            self.pixels[i] = (255, 0, 0)  # Red
            if i < self.led_count - 1:
                self.pixels[i+1] = (100, 0, 0)  # Trail
            if i < self.led_count - 2:
                self.pixels[i+2] = (30, 0, 0)  # Fade
            self.pixels.show()
            time.sleep(0.03)
    
    def _wheel(self, pos):
        """Generate rainbow colors across 0-255 positions"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)


    def _theater_chase_animation(self, color=(127, 127, 127)):
        """Marquee-style chase"""
        initial_state = self.current_state

        for q in range(3):
            if self.current_state != initial_state:
                return
            for i in range(0, self.led_count, 3):
                if i + q < self.led_count:
                    self.pixels[i + q] = color
            self.pixels.show()
            time.sleep(0.05)
            for i in range(0, self.led_count, 3):
                if i + q < self.led_count:
                    self.pixels[i + q] = (0, 0, 0)
    
    def cleanup(self):
        """Stop animations and turn off LEDs"""
        self.running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=2)
        self.pixels.fill((0, 0, 0))
        self.pixels.show()



def LEDs_control(gpio, data):
    
    state = data.strip('<>')
    gpio.set_state(state)




# def setup_button(pin_number):
#     """Initializes and returns a button object using digitalio."""
#     button_pin = getattr(board, f'D{pin_number}') # Converts pin number to board object, e.g., 23 -> board.D23
#     button = digitalio.DigitalInOut(button_pin)
#     button.direction = digitalio.Direction.INPUT
#     button.pull = digitalio.Pull.UP
#     button.state = button.value
#     return button


# def check_if_talk(button):
#     current_state = button.value
    
#     # Check if state changed
#     if current_state != button.state:
#         button.state = current_state
#         return True  # State changed!
    
#     return False  # No change
    

#Global state tracking
_button_initialized = False
_last_button_state = None
_button_pin = None 
_debounce_time = 0.05 # 50 milisec
    
def check_if_talk(gpio):
    global _button_initialized, _last_button_state, _button_pin



    # Initialize on first call
    if not _button_initialized:
        #print("------------------------ GPIO TOUCH INITIALISATION")
        _button_pin = gpio['touch']
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        _last_button_state = GPIO.input(_button_pin)
        _button_initialized = True
        return False  # No change on first call
    
    # Read current state
    current_state = GPIO.input(_button_pin)
    print("checking button press ..............................")

    # Check if state changed
    if current_state != _last_button_state:
        print("button state changed :)))))")

        # State has changed! But is it noise? Wait a moment and check again.
        time.sleep(_debounce_time)
        new_current_state = GPIO.input(_button_pin)
        
        if current_state == new_current_state:
            print("Button WAS ACTUALLY PRESSED")
            _last_button_state = current_state
            _button_initialized = None ## dirty hack to handle the situation with press-release buttons
            return True  # State changed!
    
    return False  # No change


def cleanup():
    """Call this when your program exits"""
    GPIO.cleanup()