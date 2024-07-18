# XCSoar Landout images

[XCSoar](https://www.xcsoar.org/) is an Android app for glider pilots. [landout.streckenflug.at](https://landout.streckenflug.at) is a community-maintained list of fields for out landing. The code in this repository downloads the data from landout.streckenflug.at and puts it into a format that can be loaded into XCSoar.

Below is what it looks like in XCSoar. When you click on a field and select _Details_, then click on the left arrow button at the bottom of the screen, you see the following:

![Waypoint image in XCsoar](screenshots/field-picture.jpg?raw=true "Waypoint image in XCSoar")

## Installation in XCSoar

1. Download the CUP file for the region you are interested in from https://landout.streckenflug.at//index.php?inc=cup (English) or https://landewiesen.streckenflug.at//index.php?inc=cup (German). This for example gives you the file `zentral_und_ostalpen_de.cup`.

2. Download the ZIP file from the GitHub Releases page of this project. This should contain a `.txt` file with the same name as the CUP file. For example, `zentral_und_ostalpen_de.txt`. It also contains a folder `images` with a subfolder with the same name. For example, `images/zentral_und_ostalpen_de`.

3. Copy the `.cup` and `.txt` file, as well as the `images` folder into XCSoar's data directory on your phone. For example, into `/sdcard/Android/data/org.xcsoar/files`. In this example, the `images` folder must then exist at `.../files/images`. You don't need to include all subdirectories of the `images` folder. It is enough to only include the subdirectory for your region.

4. Open XCSoar and go to _Config_ / _System_ / _Site Files_. Select the `.cup` file as the "More waypoints" file and the `.txt` file as the "Waypoint details" file.

5. Restart XCSoar.

6. It can now happen that XCSoar no longer displays airfields. This is because the built-in map databases also contain this information, but XCSoar does not display it when a custom Waypoints file is given. To fix this, you need to manually supply a "Waypoints" file with the airfields for your region. (Remember that we filled in the "More waypoints" field above.)

7. Restart XCSoar.

You should now be able to view the approach images for landout fields by following the instructions at the top of this document.

## Running the code

You need Python 3 and Chrome installed to run this code. First, set up a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
# On Mac/Linux:
source venv/bin/activate
# On Windows:
call venv\scripts\activate.bat
```

(The code has not been tested on Windows and may not work there without modifications.)

Install the necessary dependencies:

```bash
python3 -m pip install -Ur requirements.txt
```

Now, to run the code, you need to supply the path to a `.cup` file from landout.streckenflug.at. For example:

```bash
python3 main.py /path/to/zentral_und_ostalpen_de.cup
```

This produces the `zentral_und_ostalpen_de.txt` file and the `images/` directory next to the `.cup` file.

### A big caveat

When you run the script, some images sometimes do not load properly. They remain grey, or show some grey squares:

![Landout field with grey squares](screenshots/grey-squares.jpg?raw=true "Landout field with grey squares")

You must check that the images in the `images/` folder do not exhibit this problem. (It is easy to do when you look at the thumbnails.) If an image is broken in this way, delete it and run the script again. The script will then only re-download this one image, and not the others.

## Contributing

Please donate to https://landout.streckenflug.at/. You can find simple instructions on their website.

Contributions are welcome. Please follow my [PR guidelines](https://gist.github.com/mherrmann/5ce21814789152c17abd91c0b3eaadca).