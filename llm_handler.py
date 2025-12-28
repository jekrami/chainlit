import requests
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import (
    PRIMARY_LEGAL_ANALYST_MODEL,
    SECONDARY_VERIFICATION_MODEL,
    SYNTHESIZER_MODEL,
    OLLAMA_API_ENDPOINT,
    LLM_TEMPERATURE,
    LLM_TOP_P
)

# Create a thread pool executor to run synchronous requests in a non-blocking way
executor = ThreadPoolExecutor(max_workers=5)

class LlmHandler:
    def _query_model_sync(self, model_name, prompt):
        """Synchronous function to query the Ollama model."""
        try:
            response = requests.post(
                OLLAMA_API_ENDPOINT,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": LLM_TEMPERATURE,
                        "top_p": LLM_TOP_P,
                    },
                },
                timeout=180,  # Increased timeout for potentially long legal analysis
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.RequestException as e:
            error_message = f"Error querying model {model_name}: {e}"
            print(error_message)
            return f"خطا در ارتباط با مدل {model_name}. جزئیات فنی: {e}"

    async def _query_model_async(self, model_name, prompt):
        """Asynchronous wrapper to run the synchronous query in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor, self._query_model_sync, model_name, prompt
        )

    async def get_synthesized_answer(self, question, context):
        # Prompt for the legal analyst and verifier models
        base_prompt = f"""
        **دستورالعمل:** شما یک تحلیلگر حقوقی متخصص در قوانین ایران هستید. بر اساس متن قرارداد زیر، به سوال کاربر با دقت و به صورت رسمی پاسخ دهید. فقط از اطلاعات موجود در متن استفاده کنید. پاسخ شما باید دقیق، مبتنی بر واقعیت و متمرکز بر بندهای قرارداد باشد. از ارائه مشاوره حقوقی خودداری کنید.

        **متن قرارداد (زمینه):**
        ---
        {context}
        ---

        **سوال کاربر:** {question}

        **پاسخ شما (به فارسی رسمی و با ارجاع به مواد قرارداد در صورت امکان):**
        """

        # Run model queries in parallel
        tasks = [
            self._query_model_async(PRIMARY_LEGAL_ANALYST_MODEL, base_prompt),
            self._query_model_async(SECONDARY_VERIFICATION_MODEL, base_prompt),
        ]

        responses = await asyncio.gather(*tasks)
        analyst_response, verifier_response = responses

        # Prompt for the synthesizer model
        synthesis_prompt = f"""
        **دستورالعمل:** شما یک متخصص ارشد حقوقی و ویراستار نهایی هستید. دو تحلیل از یک قرارداد توسط دو مدل هوش مصنوعی در زیر ارائه شده است. وظیفه شما ترکیب این دو تحلیل، حل هرگونه اختلاف، و ارائه یک پاسخ نهایی، دقیق، و محافظه‌کارانه به زبان فارسی رسمی است. پاسخ نهایی باید اعداد، تاریخ‌ها و جزئیات کلیدی را با دقت حفظ کند و هرگونه اطلاعات متناقض یا حدسی را حذف نماید. پاسخ نهایی باید یکپارچه و منسجم باشد.

        **تحلیل مدل اول (تحلیلگر اصلی):**
        ---
        {analyst_response}
        ---

        **تحلیل مدل دوم (تاییدکننده):**
        ---
        {verifier_response}
        ---

        **سوال اصلی کاربر:** {question}

        **پاسخ نهایی ترکیبی و ویراسته (به فارسی رسمی و حقوقی):**
        """

        final_answer = await self._query_model_async(SYNTHESIZER_MODEL, synthesis_prompt)
        return final_answer
