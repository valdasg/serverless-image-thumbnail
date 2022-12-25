# Thumbnail app for S3

This app generates a thumbnail as the png file is uploaded to s3 bucket.
Metadada is stored in Dynamo DB and is retrieved by API.

App is created using Serverless Framework on AWS platfrom.

## Usage
Upload image to S3 and thumbnail file gets generated with '_thumbnail.png' suffix.

### Deployment
Third-party dependencies are used in app, so you will need to use a plugin `serverless-python-requirements`. You can set it up by running the following command:

```bash
serverless plugin install -n serverless-python-requirements
```

In order to deploy app you need to clone and run the following command from parrent folder:

```
$ serverless deploy
```
Framework creates s3 bucket, lambda functions, iam role and api service.

### Clean up
After playing with app, delete contents of S3 bucket and run:

```
sls remove
```