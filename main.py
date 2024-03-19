from diffusers import AutoPipelineForText2Image
import torch
from PIL import Image
from IPython.display import display
import argparse


def read_input():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--prompt', type=str, help='Description of parameter 1')
    parser.add_argument('--negative_prompt', type=str,default='', help='Description of parameter 2 (optional)')
    parser.add_argument('--model', type=str,default='', help='Description of parameter 2 (optional)')
    return parser.parse_args()



def load_pipeline(model):
    pipeline = AutoPipelineForText2Image.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16).to("cuda")
    
    # Load weights
    pipeline.load_lora_weights(
        "/home/",
        weight_name="prav_r128_sdxl.safetensors",
        adapter_name="man"
    )
    return pipeline


def generate_image_from_prompt():
    # Initialize pipeline
    request  = read_input()
    pipeline = load_pipeline(request.model)
    images = pipeline(
        prompt= request.prompt,
        negative_prompt=request.negative_prompt,
        height=1024,
        width=1024
    ).images

    # Save and display image
    images[0].save('/home/outputs.jpg')


generate_image_from_prompt()
