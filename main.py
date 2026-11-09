"""
Geospatial Vegetation Change Analysis
Thrissur Kole Wetlands, Kerala

Run this file once from the project folder:
    python main.py

It creates the required project folders and generates:
    notebooks/geospatial_analysis.ipynb

The satellite data download and analysis are performed when you run all
cells inside the generated Jupyter notebook.
"""

import sys
from pathlib import Path

try:
    import nbformat as nbf
except ImportError:
    sys.exit(
        "Missing dependency: nbformat. Install the project requirements first:\n"
        "    python -m pip install -r requirements.txt"
    )

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- notebook cells
CELLS = []
md = lambda s: CELLS.append(("md", s))
code = lambda s: CELLS.append(("code", s))

md(r"""# Two-Date Vegetation Comparison: Thrissur Kole Wetlands
Sentinel-2 L2A, January 2024 vs January 2026. Steps: download data, inspect, preprocess, map the study area, compute NDVI, compare, statistics, conclusion.""")

md(r"""## 1. Setup
Imports, folder paths and the study area bounding box (west, south, east, north in lon/lat).""")
code(r'''from pathlib import Path
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import rasterio, geopandas as gpd, folium
from shapely.geometry import box

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
DATA, OUT = ROOT / "data", ROOT / "outputs"
for y in (2024, 2026):
    (DATA / str(y)).mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

BBOX = [76.10, 10.40, 76.22, 10.50]   # Kole wetlands area, adjust if you like
MAX_CLOUD = 20                        # raise to 40 if no scene is found
print("Project root:", ROOT)''')

md(r"""## 2. Download Sentinel-2 L2A data
Searches the Planetary Computer catalog for the least cloudy January scene in each year. The 2026 scene must come from the same MGRS tile as 2024 so both dates share one pixel grid. Bands B02, B03, B04 and B08 are cut to the study area and saved to `data/2024/` and `data/2026/`. If the files already exist, nothing is downloaded again.""")
code(r'''import planetary_computer as pc
from pystac_client import Client
from shapely.geometry import shape
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
BANDS = ("B02", "B03", "B04", "B08")
aoi = box(*BBOX)

def find(catalog, dt, tile=None):
    items = catalog.search(collections=["sentinel-2-l2a"], bbox=BBOX, datetime=dt,
                           query={"eo:cloud_cover": {"lt": MAX_CLOUD}}).item_collection()
    items = [i for i in items if shape(i.geometry).contains(aoi)
             and (tile is None or i.properties["s2:mgrs_tile"] == tile)]
    return sorted(items, key=lambda i: i.properties["eo:cloud_cover"])

def save_bands(item, year):
    for b in BANDS:
        out = DATA / str(year) / f"{b}.tif"
        if out.exists():
            continue
        with rasterio.open(item.assets[b].href) as src:
            w = from_bounds(*transform_bounds("EPSG:4326", src.crs, *BBOX), transform=src.transform)
            w = Window(int(np.floor(w.col_off)), int(np.floor(w.row_off)),
                       int(np.ceil(w.width)), int(np.ceil(w.height)))
            arr = src.read(1, window=w)
            prof = src.profile.copy()
            for k in ("blockxsize", "blockysize", "tiled"):
                prof.pop(k, None)
            prof.update(driver="GTiff", height=arr.shape[0], width=arr.shape[1],
                        transform=src.window_transform(w), compress="deflate")
            with rasterio.open(out, "w", **prof) as dst:
                dst.write(arr, 1)
        print("saved", out.relative_to(ROOT))

need = [DATA / y / f"{band}.tif" for y in ("2024", "2026") for band in BANDS]
if not all(p.exists() for p in need):
    catalog = Client.open(STAC, modifier=pc.sign_inplace)
    c24 = find(catalog, "2024-01-01/2024-01-31")
    assert c24, "No 2024 scene found. Raise MAX_CLOUD."
    for cand in c24:
        c26 = find(catalog, "2026-01-01/2026-01-31", tile=cand.properties["s2:mgrs_tile"])
        if c26:
            best24, best26 = cand, c26[0]
            break
    else:
        raise RuntimeError("No matching 2026 scene. Raise MAX_CLOUD or widen the date range.")
    print("2024 scene:", best24.id, "| cloud", best24.properties["eo:cloud_cover"])
    print("2026 scene:", best26.id, "| cloud", best26.properties["eo:cloud_cover"])
    save_bands(best24, 2024)
    save_bands(best26, 2026)
else:
    print("Data already downloaded.")''')

md(r"""## 3. Load and inspect
Opens the GeoTIFFs with Rasterio and prints size, CRS and pixel resolution.""")
code(r'''def read(year, band):
    with rasterio.open(DATA / str(year) / f"{band}.tif") as s:
        dn = s.read(1).astype("float32")
        meta = dict(shape=s.shape, crs=s.crs, res=s.res, transform=s.transform)
    return dn, meta

rows = []
for y in (2024, 2026):
    for b in ("B04", "B08"):
        _, m = read(y, b)
        rows.append({"Year": y, "Band": b, "Height x Width": m["shape"],
                     "CRS": str(m["crs"]), "Resolution (m)": m["res"]})
pd.DataFrame(rows)''')

md(r"""## 4. Preprocess
- Sentinel-2 L2A data from 2022 onward has a +1000 offset, so reflectance = (DN - 1000) / 10000.
- DN = 0 is NoData and becomes NaN.
- Check that both dates have the same CRS, shape and pixel grid.""")
code(r'''def reflectance(dn):
    return np.where(dn == 0, np.nan, np.clip((dn - 1000) / 10000, 0, 1)).astype("float32")

bands, meta = {}, {}
for y in (2024, 2026):
    bands[y] = {}
    for b in BANDS:
        dn, m = read(y, b)
        bands[y][b] = reflectance(dn)
        meta[y] = m

same_crs  = meta[2024]["crs"] == meta[2026]["crs"]
same_grid = meta[2024]["shape"] == meta[2026]["shape"] and meta[2024]["transform"] == meta[2026]["transform"]
print("Same CRS:", same_crs, "| Same shape and pixel grid:", same_grid)
assert same_crs and same_grid, "Datasets are not aligned: re-run the download cell."
print("NoData pixels 2024:", int(np.isnan(bands[2024]["B04"]).sum()),
      "| 2026:", int(np.isnan(bands[2026]["B04"]).sum()))''')

md(r"""## 5. Map 1: study area and wetland boundary (Folium)
The boundary comes from `data/study_area.geojson`. A rectangle around the study area is created automatically if the file is missing. To use a real wetland outline, draw it at geojson.io and save it over that file.""")
code(r'''GEOJSON = DATA / "study_area.geojson"
if not GEOJSON.exists():
    gpd.GeoDataFrame({"name": ["Thrissur Kole Wetlands (approx.)"]}, geometry=[aoi],
                     crs="EPSG:4326").to_file(GEOJSON, driver="GeoJSON")
area = gpd.read_file(GEOJSON).to_crs(4326)
minx, miny, maxx, maxy = area.total_bounds
cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

m = folium.Map(location=[cy, cx], zoom_start=11, tiles="OpenStreetMap")
folium.GeoJson(area.__geo_interface__, name="Wetland boundary",
               style_function=lambda f: {"color": "red", "weight": 3, "fillOpacity": 0.1}).add_to(m)
folium.Marker([cy, cx], tooltip="Thrissur Kole Wetlands").add_to(m)
m.fit_bounds([[miny, minx], [maxy, maxx]])
folium.LayerControl().add_to(m)
m.save(OUT / "interactive_map.html")
m''')

md(r"""## 6. Maps 2 and 3: true-colour satellite images""")
code(r'''def rgb(y):
    img = np.dstack([bands[y]["B04"], bands[y]["B03"], bands[y]["B02"]])
    return np.clip(np.nan_to_num(img) / 0.3, 0, 1)

fig, ax = plt.subplots(1, 2, figsize=(14, 6))
for a, y in zip(ax, (2024, 2026)):
    a.imshow(rgb(y)); a.set_title(f"Sentinel-2 true colour, January {y}"); a.axis("off")
plt.tight_layout(); plt.savefig(OUT / "true_colour.png", dpi=200); plt.show()''')

md(r"""## 7. Maps 4 and 5: NDVI
NDVI = (NIR - Red) / (NIR + Red) using B08 and B04. Both maps use the same colour scale (-0.2 to 0.9) so they can be compared directly.""")
code(r'''def ndvi(y):
    red, nir = bands[y]["B04"], bands[y]["B08"]
    with np.errstate(divide="ignore", invalid="ignore"):
        return (nir - red) / (nir + red)

ndvi24, ndvi26 = ndvi(2024), ndvi(2026)

fig, ax = plt.subplots(1, 2, figsize=(14, 6))
for a, d, y in zip(ax, (ndvi24, ndvi26), (2024, 2026)):
    im = a.imshow(d, cmap="RdYlGn", vmin=-0.2, vmax=0.9)
    a.set_title(f"NDVI, January {y}"); a.axis("off")
fig.colorbar(im, ax=ax, shrink=0.7, label="NDVI")
plt.savefig(OUT / "ndvi_maps.png", dpi=200, bbox_inches="tight"); plt.show()''')

md(r"""## 8. Map 6: NDVI change (2026 minus 2024)
Left: continuous change. Right: classified. A change above +0.1 counts as increase, below -0.1 as decrease, anything else as little change.""")
code(r'''T = 0.1
diff = ndvi26 - ndvi24
valid = ~np.isnan(diff)

cls = np.full(diff.shape, np.nan)
cls[valid & (diff < -T)] = 0
cls[valid & (np.abs(diff) <= T)] = 1
cls[valid & (diff > T)] = 2

fig, ax = plt.subplots(1, 2, figsize=(15, 6))
im = ax[0].imshow(diff, cmap="RdBu", vmin=-0.5, vmax=0.5)
ax[0].set_title("NDVI change (2026 - 2024)"); ax[0].axis("off")
fig.colorbar(im, ax=ax[0], shrink=0.7)
ax[1].imshow(cls, cmap=ListedColormap(["#d73027", "#d9d9d9", "#1a9850"]), vmin=0, vmax=2)
ax[1].set_title("Red = decrease, grey = little change, green = increase"); ax[1].axis("off")
plt.tight_layout(); plt.savefig(OUT / "ndvi_change.png", dpi=200); plt.show()''')

md(r"""## 9. Statistics""")
code(r'''n = valid.sum()
stats = pd.DataFrame({
    "Metric": ["Mean NDVI 2024", "Mean NDVI 2026", "Mean NDVI difference",
               "% pixels increased (> +0.1)", "% pixels decreased (< -0.1)", "% pixels little change"],
    "Value": [np.nanmean(ndvi24), np.nanmean(ndvi26), np.nanmean(diff),
              (diff[valid] > T).sum() / n * 100, (diff[valid] < -T).sum() / n * 100,
              (np.abs(diff[valid]) <= T).sum() / n * 100]}).round(3)
stats.to_csv(OUT / "stats.csv", index=False)

pct = stats["Value"].iloc[3:].values
plt.figure(figsize=(6, 4))
plt.bar(["Increased", "Decreased", "Little change"], pct, color=["#1a9850", "#d73027", "#999999"])
plt.ylabel("% of pixels"); plt.title("Share of pixels by NDVI change")
plt.savefig(OUT / "change_share.png", dpi=200); plt.show()
stats''')

md(r"""## 10. Conclusion
The text below is generated from the numbers above. Edit it in your own words after looking at the maps.""")
code(r'''d24, d26, dd = np.nanmean(ndvi24), np.nanmean(ndvi26), np.nanmean(diff)
trend = "increased" if dd > 0 else "decreased"
print(f"Mean NDVI {trend} from {d24:.3f} (Jan 2024) to {d26:.3f} (Jan 2026), a change of {dd:+.3f}.")
print(f"{pct[0]:.1f}% of pixels show increased vegetation, {pct[1]:.1f}% decreased, "
      f"and {pct[2]:.1f}% changed little.")''')

md(r"""**Interpretation (write your own after viewing the maps):** Describe where vegetation increased or decreased and why this might be. In Kole wetlands, January NDVI depends strongly on the paddy crop stage and standing water, so a difference between two single dates may reflect different planting schedules rather than a long-term trend. Using more dates (for example monthly composites across several years) would give a firmer conclusion.""")

# ---------------------------------------------------------------- write notebook
def main():
    """Create the project folders and generate the analysis notebook."""
    for folder in ("data/2024", "data/2026", "notebooks", "outputs"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)

    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(text) if kind == "md"
        else nbf.v4.new_code_cell(text)
        for kind, text in CELLS
    ]
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }

    notebook_path = ROOT / "notebooks" / "geospatial_analysis.ipynb"
    nbf.write(nb, notebook_path)

    print("\\nProject setup completed successfully.")
    print("Created folders: data/2024, data/2026, notebooks, outputs")
    print(f"Created notebook: {notebook_path.relative_to(ROOT)}")
    print("\\nNext, run this command to open the notebook:")
    print("jupyter notebook notebooks/geospatial_analysis.ipynb")
    print("\\nIn Jupyter, open the notebook and choose Kernel > Restart & Run All.")


if __name__ == "__main__":
    main()
