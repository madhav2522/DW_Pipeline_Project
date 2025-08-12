import boto3

# Initialize boto3 Glue client
glue_client = boto3.client('glue', region_name='us-east-2')

# Name of the Glue Crawler
crawler_name = 'dw-pipeline-crawler'  # Replace with your actual crawler name

# Start the Glue Crawler
response = glue_client.start_crawler(Name=crawler_name)

# Check if the crawler started successfully
if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print(f"Crawler {crawler_name} started successfully!")
else:
    print(f"Failed to start the crawler {crawler_name}.")
