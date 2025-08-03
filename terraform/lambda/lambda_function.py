def lambda_handler(event, context):
    """
    SmartCloudOps AI ML Processor Lambda Function
    
    This function handles ML model training and inference tasks.
    It can be triggered by various AWS events like S3 uploads, CloudWatch events, etc.
    """
    import json
    import boto3
    import os
    
    # Initialize AWS clients
    s3_client = boto3.client('s3')
    
    # Get environment variables
    ml_models_bucket = os.environ.get('S3_ML_MODELS_BUCKET')
    logs_bucket = os.environ.get('S3_LOGS_BUCKET')
    
    try:
        # Process the event
        print(f"Processing event: {json.dumps(event)}")
        
        # Example: Handle S3 event for new data uploads
        if 'Records' in event:
            for record in event['Records']:
                if record.get('eventSource') == 'aws:s3':
                    bucket = record['s3']['bucket']['name']
                    key = record['s3']['object']['key']
                    print(f"Processing S3 object: s3://{bucket}/{key}")
                    
                    # Add your ML processing logic here
                    result = process_ml_data(bucket, key, s3_client)
                    
                    # Store results in logs bucket
                    if logs_bucket:
                        store_results(result, logs_bucket, s3_client)
        
        # Example: Handle direct invocation for model training
        elif event.get('action') == 'train_model':
            print("Starting model training...")
            result = train_anomaly_detection_model(ml_models_bucket, s3_client)
            
        # Example: Handle inference requests
        elif event.get('action') == 'predict':
            print("Running inference...")
            result = run_inference(event.get('data'), ml_models_bucket, s3_client)
            
        else:
            result = {
                'message': 'SmartCloudOps AI ML Processor is running',
                'timestamp': context.aws_request_id
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'result': result
            })
        }
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def process_ml_data(bucket, key, s3_client):
    """Process incoming data for ML pipeline"""
    # Placeholder for data processing logic
    print(f"Processing data from s3://{bucket}/{key}")
    return {
        'processed_file': f"s3://{bucket}/{key}",
        'status': 'processed'
    }

def train_anomaly_detection_model(bucket, s3_client):
    """Train the anomaly detection model"""
    # Placeholder for model training logic
    print(f"Training model, storing in bucket: {bucket}")
    return {
        'model_location': f"s3://{bucket}/models/anomaly_model.pkl",
        'training_status': 'completed'
    }

def run_inference(data, bucket, s3_client):
    """Run inference using trained model"""
    # Placeholder for inference logic
    print(f"Running inference with model from bucket: {bucket}")
    return {
        'prediction': 'normal',
        'confidence': 0.95
    }

def store_results(result, bucket, s3_client):
    """Store processing results in S3"""
    try:
        import json
        from datetime import datetime
        
        timestamp = datetime.utcnow().isoformat()
        key = f"results/{timestamp}-result.json"
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(result),
            ContentType='application/json'
        )
        print(f"Results stored at s3://{bucket}/{key}")
    except Exception as e:
        print(f"Error storing results: {str(e)}")
