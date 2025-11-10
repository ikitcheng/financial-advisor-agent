'''
Reference: https://github.com/MetaGLM/zhipuai-sdk-python-v4/blob/main/README.md
Get Zhipuai API key here: https://open.bigmodel.cn/login 
'''
from zhipuai import ZhipuAI
import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))

def ask_zhipuai(messages: list, model="glm-4-flash"):
    """
    Send messages to Zhipu AI and return the response.
    
    Args:
        messages: List of message dictionaries, e.g., 
                 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        model: The model to use (default: "glm-4")
    
    Returns:
        str: The AI's response content
    """       

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    if len(response.choices) > 0:
        return response.choices[0].message.content 
    else:
        return "Error: No response generated"

def quick_test():
    """Quick test to verify the API is working"""
    print("🔥 Running quick smoke test...")
    
    test_message = [{"role": "user", "content": "Reply with just 'OK'"}]
    
    try:
        response = ask_zhipuai(test_message)
        print(f"Response: {response}")
        print("✅ Smoke test passed - API is responsive")
        return True
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False

if __name__ == "__main__":
    quick_test()