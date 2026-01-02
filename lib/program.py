from lib.iot_manager_client import IotManagerClient
from lib.wifimgr import WifiManager
import time
import ntptime
import camera
import machine
from machine import Pin
import esp32

TEST_MODE = False

class MainProgram:
    def __init__(self, iot_manager_base_url, device_id, device_password):
        self.pir = Pin(13, Pin.IN, Pin.PULL_UP)
        self.iot_manager_base_url = iot_manager_base_url
        self.device_id = device_id
        self.device_password = device_password
        self.client = IotManagerClient(base_url=self.iot_manager_base_url)
        self.wifi_manager = WifiManager()
        print("MainProgram initialized with device ID:", self.device_id)

    def connect_wifi(self, enter_captive_portal_if_needed):
        print("Connecting to WiFi...")
        wlan = self.wifi_manager.get_connection(enter_captive_portal_if_needed=enter_captive_portal_if_needed)
        if wlan is None:
            print("Could not initialize the network connection.")
            while True:
                pass

        print("Network connected:", wlan.ifconfig())
        try:
            ntptime.settime()
            print("System time synchronized:", time.time())
        except Exception as e:
            print("Failed to synchronize time:", e)
        
        return wlan
        


    def take_photo(self):
        try:
            print("Taking photo...")
            camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
            camera.framesize(camera.FRAME_SXGA)
            camera.whitebalance(camera.WB_SUNNY)
            frame = camera.capture()
            camera.deinit()
            print("Photo taken, size:", len(frame))
            return frame
        except Exception as e:
            print("create_content failed:", e)

    def upload_photo(self, frame, test_post=False):
        try:
            response = self.client.upload_image(
                image_data=frame,
                test_post=test_post,
            )
            print("Photo uploaded, server response:", response)
            return response
        except Exception as e:
            print("upload_photo failed:", e)

    def fetch_config(self):
        try:
            config = self.client.get_config()
            print("Configuration fetched:", config)
            return config
        except Exception as e:
            print("fetch_config failed:", e)
            return None

    def main(self):
        print("Starting MainProgram")
        photo = self.take_photo()
        wakeup_time = time.time()
        wake_reason = machine.wake_reason()
        print("Wake reason:", wake_reason, "at time:", wakeup_time)
        allow_captive_portal = (wake_reason != machine.DEEPSLEEP_WAKEUP_EXT0)
        wlan = self.connect_wifi(enter_captive_portal_if_needed=allow_captive_portal)
        
        if wlan is None:
            print("Failed to connect to WiFi.")
            raise Exception("WiFi connection failed")
        
        print("Connected to wifi. the time is now:", time.time())
        self.client.authenticate(self.device_id, self.device_password)
        self.client.discover()
        print("Connected to IoT Manager at:", self.iot_manager_base_url)

        self.upload_photo(photo)

        try:
            print("Checking for firmware updates...")
            self.client.check_and_update_firmware()
        except Exception as e:
            print("Firmware update check failed:", e)

        esp32.wake_on_ext0(pin = self.pir, level = machine.Pin.WAKE_LOW)
        self.client.create_device_status({
            "last_wakeup_time": wakeup_time,
            "last_wakeup_reason": str(wake_reason),
            "status": "sleeping",
            "version": self.client.get_firmware_version()
        })
        print("MainProgram completed. deep sleep")
        machine.deepsleep()
