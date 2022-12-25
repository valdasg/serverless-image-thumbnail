from datetime import datetime
import boto3
from io import BytesIO
from PIL import Image, ImageOps
import os
import uuid
import json

s3 = boto3.client('s3')
size = int(os.environ['THUMBNAIL_SIZE'])
dbtable = str(os.environ['DYNAMODB_TABLE'])
dynamodb = boto3.resource(
    'dynamodb', region_name = str(os.environ['REGION_NAME'])
)

def s3_thumbnail_generator(event, context):
    '''
    Function creates thumbnails from png files as files are uploadd to S3.
    '''
    print('EVENT:::', event)
    #parse event for debugging
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
    url = f'{s3.meta.endpoint_url}/{bucket}/{key}'
    s3_save_thumbnail_url_to_dynamo_db(url_path = url, img_size = img_size)

    return url

def s3_save_thumbnail_url_to_dynamo_db(url_path, img_size):
    '''
    Function creates item for dynamo db metadata.
    '''
    # creating approximate image size
    toint = float(img_size*0.53)/1000
    table = dynamodb.Table(dbtable)
    response = table.put_item(
        Item = {
            'id': str(uuid.uuid4()),
            'url': str(url_path),
            'approxReduceSize': f'{str(toint)}KB',
            'createdAt': str(datetime.now()),
            'updatedAr': str(datetime.now()),
        }
    )
    # Allways return status payload for lambda to know ok status
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
    
def s3_get_item(event, context):
    '''
    Function returns single item from dynamo db by id.
    '''
    table = dynamodb.Table(dbtable)
    # path params from serverless.yaml
    response = table.get_item(Key = {
        'id': event['pathParameters']['id']
    })
    item = response['item']
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            # indicates response can be shared with requesting code from given origin
            'Acces-Control-Allow-Oigin': '*'
        },
        'body': json.dumps(item),
        'isBase64Encoded': False
    }
    
def s3_delete_item(event, context):
    '''
    Function deletes single item from dynamo db by id.
    '''
    # path params from serverless.yaml
    item_id = event['pathParameters']['id']
    
    # default response
    response = {
        'statusCode': 500,
        'body': f'An error occured while deleting post {item_id}'
    }
    
    table = dynamodb.Table(dbtable)
    response = table.delete_item(Key = {
        'id': item_id
    })
    
    all_good_response = {
        'delted': True,
        'itemDeletedId': item_id
        
    }
    
    # if deletion is succesfull
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        response = {
            'statusCode': 200,
            'headers': {
            'Content-Type': 'application/json',
                    # indicates response can be shared with requesting code from given origin
                    'Acces-Control-Allow-Oigin': '*'
                },
                'body': json.dumps(all_good_response),
            }
        
    return response

def s3_get_thumbnail_urls(event, context):
    '''
    Function lists all urls from the db in json format
    '''
    table = dynamodb.Table(dbtable)
    response = table.scan()
    data = response['Items']
    # go through data in the loop
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey = response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }