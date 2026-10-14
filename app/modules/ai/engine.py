from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.config import settings

class AIEngine:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please add your Google Gemini API key to the backend/.env file."
                )
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7
            )
        return self._llm

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates content based on a system instruction and user input.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = self.llm.invoke(messages)
        return str(response.content)

    def refine(self, system_prompt: str, original_prompt: str, original_content: str, refinement_instruction: str) -> str:
        """
        Refines existing content based on a history of original prompt, previous content, and refinement feedback.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Original Input Prompt/Context:\n{original_prompt}\n\nPreviously Generated Content:\n{original_content}"),
            HumanMessage(content=f"Refinement Request: {refinement_instruction}\n\nPlease output the updated version matching this request.")
        ]
        response = self.llm.invoke(messages)
        return str(response.content)

ai_engine = AIEngine()
