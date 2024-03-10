import os
import datetime
import pyscreenshot as ImageGrab
screenshotNumber = 1

def take_screenshot(output_dir):
    global screenshotNumber
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = f"screenshot_{screenshotNumber}.png"
        screenshot_path = os.path.join(output_dir, filename)
        im = ImageGrab.grab()
        im.save(screenshot_path)
        screenshotNumber += 1
        return screenshot_path
    except Exception as e:
        return str(e)
