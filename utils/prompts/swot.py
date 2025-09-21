
user = ''' 
Competitors are as follows : 
{competitors}

The competitors swot data is as follows : 
{swot_data}

Questions about current company and its answers : 
{questions}

Here are the answers : 

{answers}

I want the response in JSON format only. I will parse this response and use it to generate a report.
So, make sure that the response is in JSON format only.

The format should be like this : 
{{
    "strengths": "string data",
    "weaknesses": "string data",
    "opportunities": "string data",
    "threats": "string data",
    "key_improvements": [""] # actionable items that the organization can take 
    "competitors": [""] #DO NOT MENTION THE NAME OF COMPETITORS BUT MENTION WHAT ARE SOME OF THE THINGS COMPETITORS ARE DOING
}}
'''


system = ''' 
You are a McKinsey level strategic analyst conducting a Profit Pool and Market Map analysis. Using the provided data, generate insights for visual presentation.

YOUR TASK IS TO PROVIDE ME JSON 

'''
