from diffusers import AutoPipelineForText2Image
import torch
from PIL import Image
import argparse
import time
import boto3
import secrets
from datetime import datetime
from settings import Settings 
from io import BytesIO

def read_input():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--prompt', type=str, help='Description of parameter 1')
    parser.add_argument('--negative_prompt', type=str,default='', help='Description of parameter 2 (optional)')
    parser.add_argument('--model', type=str,default='', help='Description of parameter 2 (optional)')
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

    # Upload image to Cloudflare
    job_id = uploadfile(images)
    if job_id:
          print("Image uploaded successfully to Cloudflare. Job ID:")
          print(f"https://pub-b98e7fd0839f42c4bb6c36c680b13023.r2.dev/{job_id}/0")
        
    else:
        print("Failed to upload image to Cloudflare.")
        

def list_object(prefix):
    print("i m in listing ")
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url="https://36be2b889dd21fc22f59d8342ea695fe.r2.cloudflarestorage.com/",
            aws_access_key_id=settings.CLOUDFLARE_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CLOUDFLARE_AWS_SECRET_ACCESS_KEY,
            
        )
        res = s3_client.list_objects(Bucket="photostudio", Prefix=prefix)
        print(res)
         
        urls = []
   
        for obj in res['Contents']:
            print(obj, "obg")
            file_name = obj['Key']
            print(file_name,"filename")
            url = f"https://pub-b98e7fd0839f42c4bb6c36c680b13023.r2.dev/{file_name}"
            print(url)
            urls.append(url)

        # trainModel(urls)
        
    except Exception as e:
        return {"error": str(e)}
        
def get_timestamp():
    current_time = datetime.now()
    return current_time.strftime('%Y%m%d%H%M%S')


def uploadfile(images):
    s3_client = boto3.client(service_name='s3',
                             endpoint_url=Settings.CLOUDFLARE_ENDPONT_URL,
                             aws_access_key_id=Settings.CLOUDFLARE_AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=Settings.CLOUDFLARE_AWS_SECRET_ACCESS_KEY,
                             region_name='auto'
                             )

    job_id = f"{get_timestamp()}{secrets.token_urlsafe(nbytes=6)}"
    list_object(job_id)

    try:
        for i, image in enumerate(images):
            # Convert PIL Image to bytes-like object
            with BytesIO() as buffer:
                image.save(buffer, format='JPEG')
                buffer.seek(0)
                response = s3_client.upload_fileobj(buffer, job_id, str(i))

        return job_id
    except Exception as e:
        print("Error:", e)
        return False


generate_image_from_prompt()