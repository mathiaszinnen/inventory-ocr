import gradio as gr
from gradio_image_annotation import image_annotator
import yaml

def set_filepath(path, state):
    return state + [path]

def extract_layout(annotations, layout_state):
    (h,w,c) = annotations['image'].shape

    layout = []
    for box in annotations['boxes']:
        layout.append({
            'label': box['label'],
            'x': box['xmin'] / w,
            'y': box['ymin'] / h,
            'xmax': box['xmax'] / w,
            'ymax': box['ymax'] / h   
        })
    layout_file = 'layout.yaml' 
    with open(layout_file, 'w') as f:
        yaml.dump({'regions': layout}, f)
    return gr.Markdown("Layout Downloaded Succesfully"), layout_state


with gr.Blocks() as annotation_app:
    gr.Markdown("# Layout Annotation Tool")
    
    image_file = gr.State([])
    layout = gr.State(None)

    @gr.render(inputs=image_file)
    def show_image(paths):
        if len(paths) == 0:
            upload_button = gr.UploadButton("Upload Image", file_types=["image"])
            upload_button.upload(set_filepath, inputs=[upload_button, image_file], outputs=image_file)
            gr.Markdown("Please upload an image to annotate.")
        else:
            gr.Markdown("### Annotate the Image")

            annotations = image_annotator({"image": paths[0], "boxes": []}, 
                                          label_list=["Field Name"],
                                          label_colors=[(0,255,0)],
                                          boxes_alpha=0.4)
            extract_layout_button = gr.Button("Extract Layout")
            download_hidden = gr.Markdown(visible=False, elem_id="download_hidden")
            extract_layout_button.click(extract_layout, inputs=[annotations, layout], outputs=[download_hidden, layout])
