import argparse
import os
import sys
from inventory_ocr.detection import Detector, YoloImageDetector, DummyDetector
from inventory_ocr.recognition import CardRecognizer, DummyCardRecognizer, MacOSCardRecognizer, PeroCardRecognizer, MistralOCRRecognizer
from inventory_ocr.postprocessor import PostProcessor, SchmuckPostProcessor, BenchmarkingPostProcessor
from inventory_ocr.utils import has_regions_defined
from multiprocessing import Process
import platform
import appdirs
from PIL import Image
import yaml
import csv
from tqdm import tqdm

# moved to module level so multiprocessing with "spawn" can import it
def _serve_gradio(input_dir, layout_config_path):
    from inventory_ocr.annotate import create_annotation_app
    app = create_annotation_app(input_dir, layout_config_path)
    app.launch(inbrowser=True)

def pipeline(input_dir, output_dir, layout_config, detector: Detector, recognizer: CardRecognizer, postprocessor: PostProcessor):
    print(f"Processing files in directory: {input_dir}")
    
    # Load layout configuration
    with open(layout_config, 'r') as config_file:
        config_file = yaml.safe_load(config_file)
        layout_keys = config_file['regions'].keys() 

    results_csv_raw = os.path.join(output_dir, 'results_raw.csv')
    os.makedirs(output_dir, exist_ok=True)

    with open(results_csv_raw, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=['source_file', 'Gewicht'] + list(layout_keys)) # Adding Gewicht manually to make Mistral OCR work, TODO: find generic solution
        csv_writer.writeheader()

        for filename in tqdm(os.listdir(input_dir)):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                continue
            file_path = os.path.join(input_dir, filename)
            image = Image.open(file_path)
            detections = detector.detect(image)
            detector.crop_and_save(detections, os.path.join(output_dir, 'images'), filename)
            results = recognizer.recognize(image, filename)

            # Write raw results to CSV
            row = {'source_file': filename}
            row.update({key: results.get(key, '') for key in results.keys()})
            csv_writer.writerow(row)
        print(f"Raw extraction results written to {results_csv_raw}")
    
    final_csv_output = os.path.join(output_dir, 'results.csv')
    postprocessor.postprocess(results_csv_raw, final_csv_output)


def instantiate_recognizer(engine, layout_config, app_dir):
    if engine == 'pero':
        print("Using PeroCardRecognizer, ensure you have 'pero-ocr' installed.")
        return PeroCardRecognizer(layout_config=layout_config, app_dir=app_dir)
    elif engine == 'ocrmac':
        if not platform.system() == 'Darwin':
            raise ImportError(
                "MacOSCardRecognizer requires macOS and the 'ocrmac' package. "
                "Please run this on a Mac with 'ocrmac' installed."
            )
        print("Using MacOSCardRecognizer, ensure you are running this on a Mac with 'ocrmac' installed.")
        return MacOSCardRecognizer(layout_config=layout_config)
    elif engine == 'mistral':
        return MistralOCRRecognizer(layout_config=layout_config)
    elif engine == 'dummy':
        # Dummy recognizer for rapid development
        return DummyCardRecognizer(layout_config=layout_config)
    else: # automatic selection based on platform
        if platform.system() == 'Darwin':
            print("Using MacOSCardRecognizer, ensure you are running this on a Mac with 'ocrmac' installed.")
            return MacOSCardRecognizer(layout_config=layout_config)
        else:
            print("Using PeroCardRecognizer, ensure you have 'pero-ocr' installed.")
            return PeroCardRecognizer(layout_config=layout_config, app_dir=app_dir)


def instantiate_detector(no_detect, app_dir):
    if no_detect:
        print("Using DummyDetector.")
        return DummyDetector()
    else:
        print("Using YoloImageDetector for production mode.")
        return YoloImageDetector(resources_path=os.path.join(app_dir, "detection"))

def instantiate_postprocessor(postprocessor_choice):
    if postprocessor_choice == 'benchmark':
        print("Using BenchmarkingPostProcessor for evaluation mode.")
        return BenchmarkingPostProcessor()
    elif postprocessor_choice == 'schmuck':
        print("Using SchmuckPostProcessor for mode.") 
        return SchmuckPostProcessor()
    else:
        print("Using default PostProcessor.")
        return PostProcessor()

def main():
    parser = argparse.ArgumentParser(description="Inventory Card OCR Pipeline")
    parser.add_argument(
        "input_dir",
        type=str,
        help="Path to the input directory containing files to process."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join(os.getcwd(), "output"),
        help="Path to the output directory. Defaults to './output' in the current working directory."
    )
    parser.add_argument(
        '--layout_config',
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'regions.yaml'),
        required=False,
        help="Path to the layout configuration file (YAML). Defaults to 'config/regions.yaml' relative to the project root."
    )
    parser.add_argument(
        '--ocr_engine',
        type=str,
        choices=['auto','ocrmac', 'pero', 'dummy','mistral'],
        default='auto',
        help="Recognition engine to use: 'ocrmac', 'pero', or 'dummy'. Default is 'auto', " \
        "which resolves to ocrmac when running on a mac system and pero else."
    )
    parser.add_argument(
        '--no_detect',
        action='store_true',
        help="If set, skips the detection and cropping of photographs on the photographs."
    )
    parser.add_argument(
        '--postprocessor',
        help='Set custom postprocessor, resolves to default postprocessing (only removes header names) if not set.',
        choices=['schmuck','benchmark'],
        required=False
    )
    parser.add_argument(
        '--annotate',
        help="Launch the layout annotation tool instead of running the OCR pipeline.",
        action='store_true'
    )
    args = parser.parse_args()

    # use module-level _serve_gradio (required for multiprocessing spawn)
    if args.annotate or not has_regions_defined(args.layout_config):
        p = Process(target=_serve_gradio, args=(args.input_dir, args.layout_config))
        p.start()
        p.join()

    app_dir = appdirs.user_data_dir("inventory_ocr")
    recognizer = instantiate_recognizer(args.ocr_engine, args.layout_config, app_dir)
    detector = instantiate_detector(args.no_detect, app_dir)
    postprocessor = instantiate_postprocessor(args.postprocessor)

    input_dir = args.input_dir
    output_dir = args.output_dir

    pipeline(input_dir, output_dir, args.layout_config, detector, recognizer, postprocessor)layout_config, detector, recognizer, postprocessor)

    # Check if the input directory exists
    if not os.path.isdir(input_dir):isdir(input_dir):
        print(f"Error: The directory '{input_dir}' does not exist.", file=sys.stderr)        print(f"Error: The directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)        sys.exit(1)




    main()if __name__ == "__main__":if __name__ == "__main__":
    main()