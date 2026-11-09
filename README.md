# Geospatial Vegetation Analysis

## Thrissur Kole Wetlands, Kerala

This project compares vegetation in the Thrissur Kole Wetlands using
Sentinel-2 satellite images from **January 2024** and **January 2026**.

The analysis creates satellite image comparisons, NDVI maps, a
vegetation-change map, summary statistics and an interactive study-area
map.

You do not need to download satellite images manually. The notebook
searches for suitable images and downloads the required bands
automatically when you run the analysis for the first time.

------------------------------------------------------------------------

## 1. What you need

-   Windows 10 or 11
-   Python **3.11**
-   An internet connection for the first analysis run

Download and install Python 3.11 from:

https://www.python.org/downloads/

During installation, select **Add Python to PATH**.

## 2. Project files

Keep these three files together in one folder. For example, name the
folder `Geospatial_Notebook`.

-   `main.py` --- prepares the project and creates the Jupyter notebook.
-   `requirements.txt` --- lists the Python libraries required by the
    project.
-   `README.md` --- these instructions.

The `data`, `notebooks` and `outputs` folders will be created
automatically. You do not need to create them yourself.

## 3. Run the project (Windows)

**Step 1 --- Open Command Prompt in the project folder**

Open the folder containing the three files. Click the address bar in
File Explorer, type `cmd`, and press Enter.

**Step 2 --- Create a Python environment**

Run:

``` bash
py -3.11 -m venv .venv
```

**Step 3 --- Activate the environment**

``` bash
.venv\Scripts\activate
```

You should see `(.venv)` at the beginning of the command prompt.

**Step 4 --- Install the required libraries**

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This may take a few minutes. Geospatial libraries such as Rasterio and
GeoPandas can take longer to install.

**Step 5 --- Prepare the notebook**

``` bash
python main.py
```

This creates the project folders and the notebook:

`notebooks/geospatial_analysis.ipynb`

**Step 6 --- Open the notebook**

``` bash
jupyter notebook notebooks/geospatial_analysis.ipynb
```

A browser tab will open. If it does not open automatically, copy the
local URL shown in Command Prompt into your browser.

**Step 7 --- Run the analysis**

In Jupyter:

1.  Open `geospatial_analysis.ipynb` if it is not already open.
2.  Select **Kernel → Restart & Run All**.
3.  Wait for the cells to finish. The first run downloads the satellite
    images, so it may take some time.

Do not close the Command Prompt window while Jupyter is running.

------------------------------------------------------------------------

## 4. Results

After the notebook finishes, the project contains:

  ---------------------------------------------------------------------
  Location                           Contents
  ---------------------------------- ----------------------------------
  `data/2024/` and `data/2026/`      Downloaded Sentinel-2 band images

  `data/study_area.geojson`          Study-area boundary used by the
                                     map

  `notebooks/`                       Generated Jupyter analysis
                                     notebook

  `outputs/interactive_map.html`     Interactive study-area map

  `outputs/true_colour.png`          Side-by-side satellite images

  `outputs/ndvi_maps.png`            NDVI maps for both dates

  `outputs/ndvi_change.png`          Vegetation-change comparison

  `outputs/change_share.png`         Chart showing the share of changed
                                     pixels

  `outputs/stats.csv`                Numerical summary of the analysis
  ---------------------------------------------------------------------

You can open `outputs/interactive_map.html` in a web browser. The PNG
images and CSV file can also be opened separately.

## 5. Data and method

The project accesses Sentinel-2 Level-2A imagery through the Microsoft
Planetary Computer STAC service. It searches for scenes in January 2024
and January 2026 with less than the configured cloud-cover limit, and
uses matching satellite tile coverage for comparison.

Vegetation is measured using the Normalized Difference Vegetation Index
(NDVI):

**NDVI = (NIR − Red) / (NIR + Red)**

The notebook uses Sentinel-2 band B08 for near-infrared and B04 for red.
It compares the 2026 NDVI with the 2024 NDVI:

-   Change greater than `+0.1`: increase
-   Change less than `-0.1`: decrease
-   Change between `-0.1` and `+0.1`: little change

## 6. Important note about the study-area boundary

If `data/study_area.geojson` is not present, the notebook creates an
approximate rectangular boundary from the configured study-area
coordinates. This rectangle is a study-area approximation; it should not
be described as an official or surveyed wetland boundary.

If an authoritative wetland boundary is available, it can be supplied as
a GeoJSON polygon in that location.

## 7. Notes and limitations

-   An internet connection is required for the initial satellite-image
    download.
-   Downloaded images are reused on later runs, so they do not need to
    be downloaded again unless the data files are removed.
-   The comparison uses one January image per year. Differences can be
    affected by crop stage, water levels, cloud or haze conditions and
    acquisition dates.
-   The results show a difference between two image dates; they do not,
    by themselves, establish a long-term wetland degradation trend.

## 8. Troubleshooting

**`py` is not recognized**

Install Python 3.11 and make sure the Python launcher is available.
Reopen Command Prompt after installation.

**`No module named ...`**

Activate the virtual environment and run:

``` bash
pip install -r requirements.txt
```

**No suitable satellite scene is found**

The notebook uses a cloud-cover limit. If no suitable scene is found,
follow the instruction printed by the notebook and adjust the
`MAX_CLOUD` setting in its setup section.

**Jupyter does not open in the browser**

Keep Command Prompt open. Copy the `http://localhost:...` address
printed there and paste it into your browser.

## 9. Writing and saving your interpretation

At the end of the notebook, the numerical conclusion is generated
automatically from the NDVI results. The **Interpretation** is the part
that the person running the analysis should write after looking at the
maps.

You do not need to edit `main.py` or any file in the project root to do
this.

### Add your interpretation in Jupyter

1.  Scroll to the final **Interpretation** section in the notebook.
2.  Click the **+** button in the toolbar to insert a new cell below it.
3.  Change the cell type from **Code** to **Markdown** using the
    cell-type dropdown in the toolbar.
4.  Type your interpretation in that cell. Mention where vegetation
    appears to have increased or decreased and possible reasons, such as
    crop stage or water levels.
5.  Press **Shift + Enter** to display the text.
6.  Press **Ctrl + S** to save the notebook.

Example text (edit it to match what you actually observe in your maps):

> The comparison shows that vegetation decreased across a larger portion
> of the study area than it increased, while most pixels showed little
> change. Differences may be related to paddy cultivation stages and
> water levels on the two image dates. Since this analysis uses only one
> image per year, it cannot by itself confirm a long-term vegetation
> degradation trend.

### Optional: save the interpretation as a separate text file

If you also need a separate conclusion file, add another **Code** cell
below your interpretation and run this code. Replace the sample text
with the interpretation you wrote:

``` python
from pathlib import Path

conclusion = """
The comparison shows that vegetation decreased across a larger portion
of the study area than it increased, while most pixels showed little change.
Differences may be related to paddy cultivation stages and water levels
on the two image dates. More dates are needed to confirm a long-term trend.
"""

output_folder = Path("outputs")
output_folder.mkdir(exist_ok=True)

(output_folder / "conclusion.txt").write_text(conclusion.strip(), encoding="utf-8")
print("Conclusion saved to outputs/conclusion.txt")
```

After running the cell, `outputs/conclusion.txt` will contain the
written interpretation. This step is optional; saving the notebook with
**Ctrl + S** already preserves the interpretation inside the notebook.
