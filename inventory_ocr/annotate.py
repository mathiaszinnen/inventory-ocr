import gradio as gr
from gradio_image_annotation import image_annotator
import os
import yaml

def create_annotation_app(input_dir, layout_file_path):
    """
    Returns a gr.Blocks app to annotate the layout. 
    TODOS: Display a nice success message and close the browser window before killing the app serving process. But gradio conditional rendering is a pain in the...
    """
    print("Loading template image for region annotation...")
    img_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    assert img_files, "No image files found in the input directory."
    template_image_path = os.path.join(input_dir, img_files[0])

    def set_layout(layout, state):
        return state + [layout]

    def extract_layout(annotations, layout_state):
        (h, w, c) = annotations['image'].shape

        regions = {}
        for box in annotations['boxes']:
            xmin = int(box['xmin']) / w
            xmax = int(box['xmax']) / w
            ymin = int(box['ymin']) / h
            ymax = int(box['ymax']) / h
            label = box['label']
            regions[label] = [xmin, ymin, xmax, ymax]
        print(f"Saving layout configuration to {layout_file_path}...")
        with open(layout_file_path, 'w') as f:
            yaml.dump({'regions': regions}, f, default_flow_style=False)
        os._exit(0) 
        return gr.Markdown("Layout succesfully defined. You may now close this window."), regions

    with gr.Blocks() as annotation_app:
        gr.Markdown("# Layout Annotation Tool")

        layout_state = gr.State([])

        gr.Markdown("### Annotate the Image")

        @gr.render(inputs=layout_state)
        def show_annotation_interface(layout):
            annotations = image_annotator({"image": template_image_path, "boxes": []},
                                            label_list=["Field Name"],
                                            label_colors=[(0, 255, 0)],
                                            boxes_alpha=0.4)
            extract_layout_button = gr.Button("Extract Layout")
            close_message =  gr.Markdown("", visible=False)
            extract_layout_button.click(extract_layout, inputs=[annotations, layout_state], outputs=[close_message, layout_state])

    return annotation_app
