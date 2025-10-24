#!/usr/bin/env python3

import re
import json

from google import genai

from fastapi import status
from fastapi.responses import JSONResponse


class NaturalLangFilter:
    """
    Natural Language Filter Parser and Context Extractor.

    Supports:
        - Detecting palindromes
        - Extracting numeric conditions (word_count, max_length, min_length)
        - Detecting character filters (contains_character)
        - Basic comparison word detection
    """

    def __init__(self):
        self.client = genai.Client(api_key="AIzaSyDxzLjorh4rE013acivV_EioV0P-DEKxxU")

    def query_json(self, query):

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
        )

        return response.text

    def parse_gemini_json(self, response_text) -> dict:
        """
        Cleans and converts a JSON string into a valid Python dictionary.
        Handles escaped characters and ensures proper JSON structure.
        """
        try:
            print("Raw response:", response_text)

            cleaned = re.sub(
                r"```json\s*(.*?)\s*```", r"\1", response_text, flags=re.DOTALL
            )
            cleaned = re.sub(r"```\s*(.*?)\s*```", r"\1", cleaned, flags=re.DOTALL)

            cleaned = cleaned.replace('\\"', '"').replace("\\n", "").strip()

            if cleaned.startswith('"') and cleaned.endswith('"'):
                cleaned = cleaned[1:-1]

            print("Cleaned JSON:", cleaned)

            try:
                return json.loads(cleaned)
            except:
                import ast

                return ast.literal_eval(cleaned)

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            return dict()
        except Exception as e:
            print(f"[parse_gemini_json] Error: {str(e)}")
            return {}

    def extract_context(self, query: str) -> dict:
        """
        Extracts structured data from a natural language query.

        Example:
            "show strings longer than 10 characters" →
            {'max_length': 10}
        """
        extracted_data = {}
        prompt = f"""
            You are a specialized **Query Constraint Extractor**. Your task is to analyze a user's request about a string or word and extract specific constraints and properties, then strictly convert them into a Python dictionary.

            ### **Extraction Rules:**

            | Constraint Key | Description | Extraction Logic & Format |
            | :--- | :--- | :--- |
            | `contains_character` | Look for a specific character or substring the user explicitly requests to be present. | Return the **exact character/substring** requested. If multiple, return the first or most prominent one. Return `None` if not found. |
            | `word_count` | Look for phrases specifying the exact number of words (e.g., "three words", "exactly 5 words"). | Return the **integer value** (e.g., `3`, `5`). Return `None` if not specified. |
            | `is_palindrome` | Look for terms like "palindrome", "reads the same forwards and backwards", or their negation (e.g., "not a palindrome"). | Return **`True`** if a palindrome is requested. Return **`False`** if "not a palindrome" is requested. Return `None` if the topic is not mentioned. |
            | `max_length` | Look for phrases indicating an upper limit on length (e.g., "at most 10 letters", "no longer than 15 characters"). | Return the **integer value** representing the maximum length. Return `None` if no maximum limit is specified. |
            | `min_length` | Look for phrases indicating a lower limit on length (e.g., "at least 5 characters", "minimum length of 8 letters"). | Return the **integer value** representing the minimum length. Return `None` if no minimum limit is specified. |

            ### **Output Format (Crucial):**

            You must return a single, valid, raw Python dictionary string. Do **not** include any explanatory text, markdown formatting (other than the code block), or conversational filler outside of this dictionary.

            **Example Target Format:**

            ```python
            {
                "contains_character": "a",
                "word_count": 3,
                "is_palindrome": False,
                "max_length": 20,
                "min_length": None
            }
            ```

            ### **User Query:**

            {query}
        """
        try:
            response = self.query_json(prompt)
            extracted_data = self.parse_gemini_json(response)
            # print('--------------filter', response_clean)
        except Exception as e:
            return {}

        return extracted_data
