from openai import OpenAI
from constants import STRATEGIC_ANALYSIS
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

with open('/Users/vivek.singh/test1/traxxia/kasnet.txt', 'r') as file:
    DATA = file.read()

resp = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "system",
            "content": f"""
                Listen up – I don't care if you're using web search, talking to aliens, or doing backflips. 
                You ALWAYS stay formal. ALWAYS. No exceptions. 
                When you get search results, you don't just copy-paste them like some rookie.
                You take that info and you present it in YOUR voice – the formal one I told you to use.
                Got it? Good.
                
                {STRATEGIC_ANALYSIS['SYSTEM']}
            """
        },
        {
            "role": "user",
            "content": f""" 
                        HERE ARE THE QUESTIONS AND THE ANSWERS FOR THE FOLLOWING COMPANY 
                        {DATA}
                        """
        }
    ],
    tools=[{"type": "web_search_preview"}]
)

# --- Extract assistant text ---
assistant_text = ""
for message in resp.output:
    if message.type == "message":
        for content in message.content:
            if content.type == "output_text":
                assistant_text += content.text + "\n"

print("==== ASSISTANT TEXT ====")
print(assistant_text)

# --- Extract web search results ---
web_search_results = []
for message in resp.output:
    if message.type == "tool" and message.tool == "web_search_preview":
        # This is where web search results appear
        web_search_results.append(message)

print("==== WEB SEARCH RESULTS ====")
print(web_search_results)
