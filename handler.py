from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json

s3 = boto3.client('s3')
size = int(os.environ['THUMBNAIL_SIZE'])

def s3_thumbnail_generator(event, context):
    #parse event
    print('EVENT:::', event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    image_size = event['Records'][0]['s3']['object']['size']

    if (not key.endswith("_thumbnail.png")):
        image = get_s3_image(bucket, key)
        thumbnail = image_to_thumbnail(image)
        thumbnail_key = new_filename(key)
        return upload_to_s3(bucket, thumbnail_key, thumbnail, image_size)

def get_s3_image(bucket, key):
    '''
    Function takes bucket as str and key as str of the S3 storage location 
    and returns open image for further processing.
    '''
    response = s3.get_object(Bucket= bucket, Key = key)
    imageContent = response['Body'].read()
    file = BytesIO(imageContent)
    return Image.open(file)

def image_to_thumbnail(image):
    '''
    Function takes image object and resizes it to thumbnail size.
    '''
    return ImageOps.fit(image,(size,size), Image.ANTIALIAS)

def new_filename(key):
    '''
    Function takes key as str and creates a new file name for thumbnail,
    adding _thumbnail.png at the end.
    '''
    key_split = key.rsplit('.', 1)
    return f'{key_split[0]}_thumbnail.png'



def upload_to_s3(bucket, key, image, img_size):
    '''
    Function saves thumbnail to memory with .png extension.
    Puts marker at 0 and uploads thumbnail to S3.
    '''
    out_thumbnail = BytesIO()
    image.save(out_thumbnail, 'PNG')
    out_thumbnail.seek(0)
    

    response = s3.put_object(
        ACL = 'public-read',
        Body = out_thumbnail,
        Bucket = bucket,
        ContentType = 'image/png',
        Key = key
    )

    print(response)

    return 's3.meta.endpoint_url, bucket, key'
