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
    parser.add_argument('--job_id', type=str, help='Description of parameter 1')
    parser.add_argument('--num_imgs', type=int,default=1, help='Description of parameter 2 (optional)')
    parser.add_argument('--negative_prompt', type=str,default='', help='Description of parameter 2 (optional)')
    parser.add_argument('--model', type=str,default='', help='Description of parameter 2 (optional)')
    parser.add_argument('--height', type=int,default=1024, help='Description of parameter 2 (optional)')
    parser.add_argument('--width', type=int,default=1024, help='Description of parameter 2 (optional)')
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
        num_images_per_prompt=request.num_imgs,
        height=request.height,
        width=request.width
    ).images


    # Upload image to Cloudflare
    job_id = uploadfile(images,request.job_id)
    if job_id:
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
        


def uploadfile(images,job_id):
    s3_client = boto3.client(service_name='s3',
                             endpoint_url=Settings.CLOUDFLARE_ENDPONT_URL,
                             aws_access_key_id=Settings.CLOUDFLARE_AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=Settings.CLOUDFLARE_AWS_SECRET_ACCESS_KEY,
                             region_name='auto'
                             )

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
