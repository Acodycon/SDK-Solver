from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
import tensorflow as tf
import numpy as np
import time

service = Service(executable_path="msedgedriver.exe")
driver = webdriver.Edge(service=service)
# WebDriverWait(driver=driver, timeout=50).until(
#     EC.presence_of_element_located((By.XPATH, "//*[@class='start-new-game-button' and @data-difficulty='extreme']"))
# )
#
# # "//"  means that the query will select the entire HTML document
# # "*"   means that the query will select all elements on the site
# # "//*" means it will search the whole site, and all contained nodes
# select_extreme_diff_button = driver.find_element(By.XPATH, "//*[@class='start-new-game-button' and @data-difficulty='extreme']")
# # So we search the entire websites for notes of the class 'start-new-game-button'
# # And of these results select the first one that has the attribute 'data-difficulty' set to 'extreme'
# select_extreme_diff_button.click()
# Alternatively, driver.get("https://sudoku.com/extreme/") would yield the same
driver.get("https://sudoku.com/extreme")  # Opens the browser window

cookie_preferences_button = WebDriverWait(driver=driver, timeout=5).until(
    # Wait for cookie preferences button to appear
    EC.presence_of_element_located((
        By.ID, "onetrust-pc-btn-handler"
    ))
)
cookie_preferences_button.click()

only_necessary_cookies = WebDriverWait(driver=driver, timeout=5).until(
    EC.presence_of_element_located((
        By.CLASS_NAME, "ot-pc-refuse-all-handler"
    ))
)
only_necessary_cookies.click()

time.sleep(3)

board = WebDriverWait(driver=driver, timeout=5).until(
    EC.presence_of_element_located((
        By.ID, "game"
    ))
)
location = board.location
size = board.size
driver.save_screenshot("screenhot.png")

x = location['x']
y = location['y']
width = location['x'] + size['width']
height = location['y'] + size['height']
print(f"width: {width}\nheight: {height}")

cell_width = int(int(width) / 9)
cell_height = int(int(height) / 9)

screenshot = Image.open("screenhot.png")
board_png = screenshot.crop((int(x), int(y), int(width), int(height)))
board_png.save("board.png")

board_converted = [[0 for i in range(9)] for j in range(9)]

xy_start = [2, 56, 110, 163, 217, 270, 325, 377, 431]
xy_stop = [54, 108, 160, 215, 268, 322, 375, 429, 483]

model = tf.keras.models.load_model("recog_model.keras")

for row in range(9):
    for col in range(9):
        cell_png = board_png.crop((xy_start[col], xy_start[row], xy_stop[col], xy_stop[row]))
        cell_png = cell_png.resize((28, 28))
        cell_png = cell_png.convert("L")
        cell_png = cell_png.point(lambda p: p > 200 and 255)
        cell_array = np.array(cell_png).reshape(1, 28, 28, 1)
        prediction = model.predict(cell_array)
        print(f"predicted value: {np.argmax(prediction)}")
        board_converted[row][col] = np.argmax(prediction)

for row in board_converted:
    print(row)
time.sleep(120)
driver.quit()  # Quits the browser window
