from argparse import ArgumentParser
from helium import start_chrome, kill_browser, go_to, get_driver, find_all, S, \
    wait_until
from os import makedirs
from os.path import join, dirname, splitext, exists, relpath
from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from time import sleep
from tqdm import tqdm
from unittest import TestCase

import csv

IMAGES_DIR = 'images'

def main():
    cup_file_path, force = parse_args()
    base_dir = dirname(cup_file_path)
    base_name = splitext(cup_file_path)[0]
    images_dir = join(base_dir, IMAGES_DIR, base_name)
    out_file = join(base_dir, splitext(cup_file_path)[0] + '.txt')
    makedirs(images_dir, exist_ok=True)
    prepare_chrome()
    try:
        with open(cup_file_path, newline='') as cup_file:
            with open(out_file, 'w') as details_file:
                reader = csv.reader(cup_file)
                rows = list(reader)
                header = rows[0]
                for row in tqdm(rows[1:]):
                    get = lambda h: row[header.index(h)]
                    url = get_field_url(get('lat'), get('lon'))
                    image_name = get('code') + '.png'
                    image_path = join(images_dir, image_name)
                    save_screenshot(url, image_path, force)
                    image_relpath = relpath(image_path, base_dir)
                    details_file.write(
                        '[' + get('name') + ']\n'
                        f'image={image_relpath}\n'
                    )
    except KeyboardInterrupt:
        pass
    finally:
        kill_browser()

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('cup_file')
    parser.add_argument('--force', help='Re-download images', action='store_true')
    args = parser.parse_args()
    return args.cup_file, args.force

def prepare_chrome(w=1000, h=1400):
    options = Options()
    options.headless = True
    options.add_argument(f"--window-size={w},{h}")
    start_chrome(options=options, headless=True)

def get_field_url(lat_str, lon_str):
    lat_deg, lat_min, lat_dir = extract_deg_mins_dir(lat_str, 2)
    lon_deg, lon_min, lon_dir = extract_deg_mins_dir(lon_str, 3)
    lat_dd = to_decimal_degrees(lat_deg, lat_min, lat_dir)
    lon_dd = to_decimal_degrees(lon_deg, lon_min, lon_dir)
    return f'https://landewiesen.streckenflug.at/index.php?inc=map#14/' + \
           f'{lat_dd:.4f}/{lon_dd:.4f}/ABCDULfos/Sat'

def extract_deg_mins_dir(coord_str, num_deg_digits):
    deg = int(coord_str[:num_deg_digits])
    mins = float(coord_str[num_deg_digits:-1])
    direction = coord_str[-1]
    return deg, mins, direction

def to_decimal_degrees(degrees, minutes, direction):
    dd = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def save_screenshot(url, path, force):
    if exists(path) and not force:
        return
    go_to(url)
    sleep(5)
    wait_until(lambda: not has_loading_tiles())
    get_driver().save_screenshot(path)
    crop_and_reduce_size(path, path, (100, 200, 800, 1300))

def has_loading_tiles():
    try:
        for e in find_all(S('.leaflet-tile')):
            if float(e.web_element.value_of_css_property('opacity')) < 1:
                return True
    except StaleElementReferenceException:
        return True
    return False

def crop_and_reduce_size(input_path, output_path, crop_box):
    with Image.open(input_path) as img:
        img = img.crop(crop_box)
        # Convert to 8 bit to reduce size:
        img_8bit = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img_8bit.save(output_path)

class ConvertCoordsTest(TestCase):
    def test_to_decimal_degrees(self):
        self.assertEqual(47.44416666666667, to_decimal_degrees(47, 26.65, 'N'))

if __name__ == '__main__':
    main()