import time
import ntptime
import machine

from environment import (
    WIFI_SSID,
    WIFI_PASSWORD,
    IOT_MANAGER_BASE_URL,
    DEVICE_ID,
    DEVICE_PASSWORD,
)

try:
    import network
except ImportError:
    network = None

from lib.iot_manager_client import IotManagerClient

def connect_wifi():
    if network is None:
        print("network module not available")
        return

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig())
        try:
            ntptime.settime()
        except Exception as e:
            print("ntptime.settime failed:", e)
        return

    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    for _ in range(30):
        if wlan.isconnected():
            print("Connected:", wlan.ifconfig())
            try:
                ntptime.settime()
            except Exception as e:
                print("ntptime.settime failed:", e)
            return
        time.sleep(0.5)

    raise RuntimeError("WiFi connection failed")

def take_photo(client):
    try:
        import camera
        print("Taking photo...")
        camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
        camera.framesize(camera.FRAME_SXGA)
        frame = camera.capture()
        camera.deinit()
        print("Photo taken, size:", len(frame))
        response = client.upload_image(
            image_data=frame,
        )
        print("Image uploaded, response:", response)
    except ImportError:
        print("camera module not available; skipping photo capture")
    except Exception as e:
        print("create_content failed:", e)

def main():
    wakeup_time = time.time()
    reason = machine.wake_reason()
    print("Wakeup time:", wakeup_time)
    print("Wake reason:", reason)

    connect_wifi()
    print("Connected to wifi. the time is now:", time.time())

    client = IotManagerClient(base_url=IOT_MANAGER_BASE_URL)
    try:
        auth = client.authenticate(DEVICE_ID, DEVICE_PASSWORD)
        print("Authenticated; Authorization:", auth)
    except Exception as e:
        print("Authenticate failed:", e)
        return
    
    try:
        client.discover()
    except Exception as e:
        print("Service discovery failed:", e)
        return

    if reason == machine.DEEPSLEEP_RESET:
        take_photo(client)
    
    # Get tomorrow's wakeup time from IoT Manager
    # Default to 24 hours later
    wakeup_time_ms = (946684800 + time.time()) * 1000 + (24 * 60 * 60 * 1000)
    print("Default wakeup time (24h later):", wakeup_time_ms)
    try:
        wakeup_time = client.get_config()
        wakeup_time_ms = wakeup_time.get('nextWakeupTimeMs')
        print("Next wakeup time from server:", wakeup_time_ms)
    except Exception as e:
        print("get_next_wakeup_time failed:", e)


    current_unix_timestamp = (946684800 + time.time()) * 1000
    print("wakeup_time_ms", wakeup_time_ms)
    print("current_unix_timestamp", current_unix_timestamp)
    ms_til_next_wakeup = wakeup_time_ms - current_unix_timestamp
    print("Milliseconds until next wakeup:", ms_til_next_wakeup)
    print("Entering deep sleep for:", ms_til_next_wakeup)
    machine.deepsleep(ms_til_next_wakeup)

main()