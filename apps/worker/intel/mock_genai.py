"""
Mock Google Generative AI SDK for development
This allows testing without the actual SDK
"""

class MockGenerativeModel:
    """Mock Gemini model"""
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def generate_content(self, prompt: str):
        """Mock content generation"""
        response = MockResponse()
        response.text = """ÖZET: Test özet
TWEET: Test tweet"""
        return response


class MockResponse:
    """Mock API response"""
    def __init__(self):
        self.text = ""


# Mock genai module
class MockGenAI:
    def configure(self, api_key: str):
        pass
    
    def GenerativeModel(self, model_name: str):
        return MockGenerativeModel(model_name)


# Export as genai
genai = MockGenAI()
