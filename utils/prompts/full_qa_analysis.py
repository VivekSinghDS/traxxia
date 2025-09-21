
user = ''' 
Here are the list of questions : 
{questions}

Here are the list of answers : 
{answers}

Analyze the question-answer pairs and return the valid status and feedback in JSON format.


'''

system = '''
You will be given a list of question-answer pairs. Your  task is to analyze all the questions and their respective answers. 
If the answer is valid for all the questions, then return {{"valid": true}} and good for market results. 
Else, return {{"valid": false, "feedback": "string data" # the string data will only contain the follow up question that they can ask the user for clarification}}
ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''
