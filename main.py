from diffusers import AutoPipelineForText2Image
import torch
from PIL import Image
import argparse
import time
import boto3
import secrets
from datetime import datetime
from .settings import Settings 


def read_input():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--prompt', type=str, help='Description of parameter 1')
    parser.add_argument('--negative_prompt', type=str, default='', help='Description of parameter 2 (optional)')
    parser.add_argument('--model', type=str, default='', help='Description of parameter 2 (optional)')
    return parser.parse_args()


def load_pipeline(model):
    pipeline = AutoPipelineForText2Image.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16).to("cuda")
    return pipeline


def generate_image_from_prompt():
    # Initialize pipeline
    request = read_input()
    pipeline = load_pipeline(request.model)
    images = pipeline(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        height=1024,
        width=1024
    ).images

    # Save and display image
    images[0].save('/home/inference/outputs.jpg')
    image_path = '/home/inference/outputs.jpg'
    print("Image generated and saved successfully.")

    # Upload image to Cloudflare
    job_id = uploadfile(image_path)
    if job_id:
        print(f"Image uploaded successfully. Job ID: {job_id}")
    else:
        print("Failed to upload image to Cloudflare.")


def get_timestamp():
    current_time = datetime.now()
    return current_time.strftime('%Y%m%d%H%M%S')

def uploadfile(image_path):
    s3_client = boto3.client(service_name='s3',
                             endpoint_url=Settings.CLOUDFLARE_ENDPONT_URL,
                             aws_access_key_id=Settings.CLOUDFLARE_AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=Settings.CLOUDFLARE_AWS_SECRET_ACCESS_KEY,
                             region_name='auto'
                             )

    job_id = f"{get_timestamp()}{secrets.token_urlsafe(nbytes=6)}"
    try:
        with open(image_path, 'rb') as f:
            response = s3_client.upload_fileobj(f, job_id, 'image.jpg')

        cloudflare_url = f"{Settings.CLOUDFLARE_ENDPONT_URL}/{job_id}/image.jpg"
        print(cloudflare_url) 
       
        return job_id
    except Exception as e:
        print(e)
        return False

generate_image_from_prompt()
