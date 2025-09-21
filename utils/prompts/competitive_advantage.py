
system = '''
You are a competitive advantage analyst. You will be given questions and answers about a company's differentiators and customer value.
Your task is to create a comprehensive competitive advantage matrix with detailed analysis of differentiators and customer choice factors.

Focus on:
1. Identification of key differentiators from Q8
2. Assessment of customer value and uniqueness
3. Evaluation of sustainability and competitive barriers
4. Analysis of customer choice reasons
5. Strategic positioning and market analysis

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

user = '''
Analyze the following questions and answers to create a competitive advantage matrix:

Questions: {questions}
Answers: {answers}

Create competitive advantage analysis and return it in the following JSON format:
{{
    "competitiveAdvantage": {{
        "differentiators": [
            {{
                "type": "", # type of differentiator like service etc 
                "description": "",
                "uniqueness": 9,
                "customerValue": 9,
                "sustainability": 7,
                "proofPoints": [
                    "Competitors lack this feature",
                    "Customer testimonials cite personal attention"
                ]
            }}
        ],
        "competitivePosition": {{
            "overallScore": "", # a value that describes how the company is performing overall
            "marketPosition": "", # a value that describes how adequately it is market positioned
            "sustainableAdvantages": 2,
            "vulnerableAdvantages": 1
        }},
        "customerChoiceReasons": [
            {{
                "reason": "Personalized attention",
                "frequency": 65,
                "linkedDifferentiator": "service"
            }}
        ]
    }}
}}

Guidelines:
- Extract differentiators from Q8 answers
- Assess uniqueness on 1-10 scale based on market comparison
- Evaluate customer value on 1-10 scale from customer feedback
- Determine sustainability on 1-10 scale (how hard to copy)
- Identify proof points that validate each differentiator
- Analyze customer choice reasons from Q8
- Calculate overall competitive position score
- Determine market position (leader/challenger/follower/nicher)
- Count sustainable vs vulnerable advantages
- Link customer choice reasons to specific differentiators
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''
