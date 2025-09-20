from api.services.groq_client import GroqClient
from api.services.xml_parser import XMLParser

# system prompt that MUST be used by Groq to produce XML only
GROQ_SYSTEM_PROMPT = """
You are an assistant that MUST always output well-formed XML and nothing else.
Root node must be <summary>.
Inside <summary>, include:
  <title> (string)
  <keyObligations> containing multiple <obligation> elements
  <risks> containing multiple <risk> elements; each <risk> must have:
      <id>, <title>, <description>, <severity> (use one of: low|medium|high|critical)
  <suggestedEdits> containing multiple <edit> elements
  <rights> containing multiple <right> elements

Each XML node must be present even if empty (provide empty tags if needed).
Return only the XML (no commentary, no JSON, no markdown).
"""


class AIAgent:
    def __init__(self, api_key=None, api_url=None):
        self.client = GroqClient(api_key=api_key, api_url=api_url)
        self.parser = XMLParser()

    def summarize_contract(self, contract_text: str, title: str = None):
        user_prompt = "Analyze the following contract and return the structured XML with root <summary>."
        if title:
            user_prompt += f"\nTitle: {title}"
        user_prompt += (
            f"\n\nContractTextStart\n{contract_text[:20000]}\nContractTextEnd"
        )

        try:
            xml = self.client.chat_completion(
                system_prompt=GROQ_SYSTEM_PROMPT, user_prompt=user_prompt
            )
        except Exception as e:
            raise RuntimeError(f"AI call failed: {e}")

        # ensure xml content includes <summary>
        if "<summary" not in xml:
            raise RuntimeError("AI returned no <summary> element")

        try:
            parsed = self.parser.parse_summary(xml)
        except ValueError as e:
            raise ValueError(f"Unable to parse AI response: {e}")

        return parsed, xml  # return parsed dict + raw xml (raw xml not stored)

    def detailed_analysis(self, contract_text: str, title: str = None):
        system = (
            GROQ_SYSTEM_PROMPT
            + "\nNow produce a more thorough, clause-level analysis and expand each <risk> with concrete mitigation steps where possible."
        )
        user_prompt = "Please perform a detailed clause-level analysis and return XML as described."
        if title:
            user_prompt += f"\nTitle: {title}"
        user_prompt += (
            f"\n\nContractTextStart\n{contract_text[:20000]}\nContractTextEnd"
        )
        try:
            xml = self.client.chat_completion(system, user_prompt, max_tokens=3000)
        except Exception as e:
            raise RuntimeError(f"AI call failed: {e}")

        if "<summary" not in xml:
            raise RuntimeError("AI returned no <summary> element")

        try:
            parsed = self.parser.parse_summary(xml)
        except ValueError as e:
            raise ValueError(f"Unable to parse AI response: {e}")

        return parsed, xml
