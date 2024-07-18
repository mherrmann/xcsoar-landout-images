from argparse import ArgumentParser
from bs4 import BeautifulSoup
from functools import cache
from helium import start_chrome, kill_browser, go_to, get_driver, find_all, S, \
    wait_until
from os import makedirs
from os.path import join, dirname, splitext, exists, relpath, basename
from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException, \
    TimeoutException
from selenium.webdriver.chrome.options import Options
from tempfile import NamedTemporaryFile
from time import sleep
from tqdm import tqdm
from unittest import TestCase
from urllib.parse import urlencode

import csv
import re
import requests

IMAGES_DIR = 'images'

def main():
    cup_file_path, force = parse_args()
    base_dir = dirname(cup_file_path)
    base_name = splitext(basename(cup_file_path))[0]
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
                    image_name = get('code') + '.jpg'
                    image_path = join(images_dir, image_name)
                    save_screenshot(url, image_path, force)
                    image_relpath = relpath(image_path, base_dir)
                    details_file.write(
                        '[' + get('name') + ']\n'
                        f'image={image_relpath}\n'
                    )
                    feedbacks = get_field_feedbacks(get('name'))
                    details_file.write('\n'.join(feedbacks) + '\n')
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

def get_field_feedbacks(field_name_incl_cat_suffix):
    field_name = strip_category_suffix(field_name_incl_cat_suffix)
    # We don't supply any parameters to 'search' to improve performance: The
    # server response contains all available fields. Because we @cache it below,
    # this means that we only make a single request for all fields combined.
    all_fields = fetch_json('search')
    # Fields may be prefixes of each other. Eg. "Aich" and "Aich Assach".
    matching_fields = [
        f for f in all_fields
        if replace_german_special_chars(f['text']) == field_name
    ]
    # There may still be multiple matching fields. This for example happens for
    # Großau. It seems there was an old field, which has become unusable, and a
    # new one with the same name was created. Pick the field with the highest
    # id:
    field = sorted(matching_fields, key=lambda f: f['id'])[-1]
    field_info = fetch_json('landeplatz', id=field['id'])
    feedbacks_html = field_info['feedback']
    if not feedbacks_html:
        return []
    soup = BeautifulSoup(feedbacks_html, 'html.parser')
    return [elt.get_text() for elt in soup.find_all('p')]

def strip_category_suffix(field_name):
    m = re.search(r' \(Kat [ABC] \d\d\d\d\)$', field_name)
    if not m:
        raise ValueError(field_name)
    return field_name[:m.start()]

def replace_german_special_chars(text):
    result = text
    for umlaut, replacement in (
        ('ü', 'ue'), ('ö', 'oe'), ('ä', 'ae'),
        ('ß', 'ss')
    ):
        result = result.replace(umlaut, replacement)\
            .replace(umlaut.capitalize(), replacement.capitalize())
    return result

@cache
def fetch_json(task, **params):
    all_params = {'inc': 'map', 'task': task}
    all_params.update(params)
    url = 'https://landewiesen.streckenflug.at//json.php?' + \
          urlencode(all_params)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

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
    try:
        wait_until(has_loading_tiles, timeout_secs=2, interval_secs=.01)
    except TimeoutException:
        pass
    else:
        wait_until(lambda: not has_loading_tiles(), interval_secs=2)
    with NamedTemporaryFile(suffix='.png') as tmp_file:
        get_driver().save_screenshot(tmp_file.name)
        with Image.open(tmp_file.name) as img:
            img.crop((100, 200, 800, 1300)).save(path)

def has_loading_tiles():
    try:
        return S('.leaflet-tile[style*="opacity: 0."]').exists()
    except StaleElementReferenceException:
        return True
    return False

class ConvertCoordsTest(TestCase):
    def test_to_decimal_degrees(self):
        self.assertEqual(47.44416666666667, to_decimal_degrees(47, 26.65, 'N'))
    def test_strip_category_suffix(self):
        self.assertEqual(
            'Airstrip Kichdorfer Heide',
            strip_category_suffix('Airstrip Kichdorfer Heide (Kat A 2021)')
        )
    def test_replace_german_special_chars(self):
        self.assertEqual('Oetztal', replace_german_special_chars('Ötztal'))

if __name__ == '__main__':
    main()