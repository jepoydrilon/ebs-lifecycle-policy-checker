"""
author: adrilon
2020 April 19 Sunday
version: 1.0

This script will display EBS snapshot lifecycle policies created in an AWS account

"""

import boto3
from jinja2 import Environment, FileSystemLoader
from botocore.config import Config
import datetime
import logging
import sys

# Setup Logging
def setup_logging():
  logger = logging.getLogger()
  for h in logger.handlers:
    logger.removeHandler(h)

  h = logging.StreamHandler(sys.stdout)

  FORMAT = '%(asctime)s %(message)s'
  h.setFormatter(logging.Formatter(FORMAT))
  logger.addHandler(h)
  logger.setLevel(logging.INFO)

  return logger

def lambda_handler(event, context):
    
    boto_config = Config(retries = {'max_attempts': 25})

    ec2_client = boto3.client('ec2', 'us-east-1', config=boto_config)
    ses_client = boto3.client('ses', config=boto_config)
    logger = setup_logging()
    
    # Getting list of available regions       
    regions = [region['RegionName'] for region in \
                (ec2_client.describe_regions())['Regions']]
    
    # Set up Jinja template
    env = Environment(loader=FileSystemLoader('template'), trim_blocks=True)
    template = env.get_template('ses_email.html')
    
    policy1 = []
        
    for region in regions:
        if 'ap-east-1' not in region:
            dlm_client = boto3.client('dlm', region_name=region, config=boto_config)
            response = dlm_client.get_lifecycle_policies()
            
            logger.info("Acquiring policies in {} region...".format(region))
            
            for policies in response['Policies']:
                policy_id = policies['PolicyId']
                description = policies['Description']
                state = policies['State']
                
                final_list = {}
                final_list.update({'Policy_id' : policy_id, 'Description': description, 'State': state})
                policy1.append(final_list)
                                
    policy_test = template.render(policy = policy1)
    currDate = datetime.datetime.now().date()
    
    logger.info("Sending policy details...")
    
    # Sending EBS lifecycle policy details   
    response = ses_client.send_email(
        Source='noreply-cloudnotification@infor.com',
        Destination={
            'ToAddresses': [
                'Alfred.Drilon@infor.com',

            ],
        },
        Message={
            'Subject': {
                'Data': "Daily Health checks - Snapshot Lifecycle Review - {}".format(str(currDate)),
                'Charset': 'UTF-8'
            },
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': policy_test

                }
            }
        }
    )
    
    logger.info("Policy details sent")    