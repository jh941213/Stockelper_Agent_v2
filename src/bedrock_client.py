import os
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock

class BedrockClient:
    def __init__(
        self,
        model_id="amazon.nova-pro-v1:0"
    ):
        # 환경 변수 로드
        load_dotenv()
        
        # AWS 자격 증명 설정
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key]):
            raise ValueError("AWS 자격 증명이 환경 변수에 설정되어 있지 않습니다.")

        try:
            # AWS 세션 생성
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            
            # Bedrock 클라이언트 초기화
            self.bedrock_runtime = session.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            
            # boto3 기본 자격 증명 설정
            boto3.setup_default_session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            
            # ChatBedrock 초기화
            self.llm = ChatBedrock(
                model_id=model_id,
                client=self.bedrock_runtime,
                streaming=True,
                model_kwargs={
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                region_name=self.region_name  # 리전 명시적 설정
            )
            
        except Exception as e:
            raise Exception(f"AWS 클라이언트 초기화 중 오류 발생: {str(e)}")
    
    def chat(self, prompt: str):
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"오류 발생: {str(e)}"