# inventory-ocr

This is a tool to extract structured data from fixed layout documents such as inventory cards, inventory books or tables. It requires layout definitions provided in `inventory_ocr/config/regions.yaml`. Currently, it is optimized to work with a collection of jewelry from the Schmuckmuseum Pforzheim, but with minor adaptations it should be adaptable to other use cases. 

Specifically, to adapt this for your own data:
- Define a different document layout in `inventory_ocr/config/regions.yaml`
- Implement your own post-processing by subclassing the abstract PostProcessor class in `inventory_ocr/postprocessor.py`

## Installation

Set up your environment using your favourite environment management tool. We recommend [venv](https://docs.python.org/3/library/venv.html). 

### MacOS
Installation using `pip install inventory-ocr` will enable the usage of the apple vision API for ocr. 
### Linux/Windows
Install using `pip install inventory-ocr[pero]` or `pip install inventory-ocr[mistral]` depending on the OCR backend you want to use. 


## Usage

Invoke using `inventory-ocr <input folder>` with input folder specifying a path to the inventory cards to be processed. Results will be saved to `output/` relative to the current working directory.

### Command Line Arguments

```
inventory-ocr <input_dir> [options]
```

**Required Arguments:**
- `input_dir`: Path to the input directory containing files to process

**Optional Arguments:**
- `--output_dir`: Path to the output directory (default: `./output`)
- `--layout_config`: Path to the layout configuration file (default: `config/regions.yaml`)
- `--annotate`: Launch the interactive layout annotation UI to create/save a regions file
- `--ocr_engine`: OCR engine to use (choices: `auto`, `ocrmac`, `pero`, `mistral`, `dummy`; default: `auto`)
- `--eval`: Run in evaluation mode (uses dummy detector and benchmarking postprocessor)

### Annotation / Generating Regions

- The repository contains an example regions file under `inventory_ocr/config/example_regions.yaml`. If present, that example will be used by default as the layout definition.
- To create your own layout interactively, run the tool with the `--annotate` flag. This launches a small Gradio UI that lets you mark regions on a template image. When you press "Extract Layout" the regions are written to the layout configuration path (see `--layout_config`, default `inventory_ocr/config/regions.yaml`) and the annotation UI will close.
- If you prefer not to use the example, simply remove `inventory_ocr/config/example_regions.yaml` (or replace it with your own `regions.yaml`), or run with `--annotate` to generate a new regions file which will be saved to the configured `--layout_config` path.

Example:
```
# use the bundled example regions (if present)
inventory-ocr ./data

# interactively generate and save regions to the default config path
inventory-ocr ./data --annotate

# specify a custom path for the generated regions
inventory-ocr ./data --annotate --layout_config ./my_regions.yaml
```

Generated YAML uses a top-level `regions:` mapping where each field name maps to a 4-element list `[x1, y1, x2, y2]` with normalized coordinates (0..1).

### Supported OCR Engines

The tool supports multiple OCR engines with automatic platform-based selection:

- **PERO OCR** (`pero`): Default for non-macOS platforms
- **Apple Vision API** (`ocrmac`): Default for macOS platforms  
- **Mistral OCR** (`mistral`): AI-powered OCR using Mistral models
- **Dummy** (`dummy`): For development and testing purposes
- **Auto** (`auto`): Automatically selects `ocrmac` on macOS, `pero` on other platforms

### Installing Optional Dependencies

Different OCR engines require additional dependencies:

**For PERO OCR (non-macOS default):**
```bash
pip install inventory-ocr[pero]
```

**For Mistral OCR:**
```bash
pip install inventory-ocr[mistral]
```

You'll also need to obtain a Mistral API key and store it in a `.env` file in your project root:

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and replace `INSERT_YOUR_KEY_HERE` with your actual Mistral API key:
   ```
   MISTRAL_API_KEY=your_actual_api_key_here
   ```

**Note:** Never share your API key publicly or commit it to version control.

**For Apple Vision API (macOS only):**
The `ocrmac` package is automatically installed on macOS systems. No additional installation required.

**Note:** The `auto` engine selection will use Apple Vision API on macOS (if available) and PERO OCR on other platforms.

## Configuration

### Region Definition

Regions (in relative coordinates) and field names are stored in `inventory_ocr/config/regions.yaml` (or the path you pass via `--layout_config`) and can be adapted according to the use case.

The region definition format uses normalized coordinates where each region is defined as `[x1, y1, x2, y2]` with values between 0 and 1:
- `x1, y1`: Top-left corner coordinates (relative to document width and height)
- `x2, y2`: Bottom-right corner coordinates (relative to document width and height)

custom_header_mappings:
  am: 'erworben am'  # Maps "am" field to "erworben am" in output
