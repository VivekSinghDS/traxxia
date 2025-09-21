
user = """
        Analyze the following question and answer pair. Determine if the answer is valid for 
        competitor analysis or not
        
        Question: {question}
        Answer: {answer}
        
        Respond with JSON format only:
        - If the answer is valid: {{"valid": true}}
        - If the answer is invalid: {{"valid": false, "feedback": "string data" # the string data will only contain the follow up question that they can ask the user for clarification}}
        
        Focus on:
        - Accuracy of the answer
        - Relevance to the question
        - Completeness of the response
        - Logical consistency
        
        
        """
        
system = """
You are a helpful assistant that analyzes question-answer pairs and provides validation feedback in JSON format. USE ONLY JSON FORMAT AND NOTHING ELSE. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
"""
