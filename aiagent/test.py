import os
from openai import OpenAI

client = OpenAI(
    # 从环境变量中读取您的方舟API Key
    api_key="2df88fd4-f74b-4bf0-b85b-a8c6ca31e736",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 深度推理模型耗费时间会较长，建议您设置一个较长的超时时间，推荐为30分钟
    timeout=1800,
)
response = client.chat.completions.create(
    # 替换 <Model> 为模型的Model ID
    model="deepseek-r1-distill-qwen-7b-250120",
    messages=[
        {"role": "user", "content": "我要有研究推理模型与非推理模型区别的课题，怎么体现我的专业性"}
    ]
)
# 当触发深度推理时，打印思维链内容
if hasattr(response.choices[0].message, 'reasoning_content'):
    print(response.choices[0].message.reasoning_content)
print(response.choices[0].message.content)
