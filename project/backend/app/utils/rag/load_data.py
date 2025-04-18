import json
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
import openai
load_dotenv("./app/routes/.env")
qianfan_api_key = os.getenv("QIANFAN_API_KEY")

def load_skeleton_keypoint(file_path="./app/utils/video/output_pose/user_3/results_20250403142257431.json"):
    with open(file_path, 'r') as file:
        data = json.load(file)
    instance_info = data.get('instance_info', [])
    meta_info = data.get('meta_info', {})
    return instance_info, meta_info


