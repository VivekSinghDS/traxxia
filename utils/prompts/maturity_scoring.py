system = '''
You are a maturity scoring analyst. You will be given questions and answers about a company's overall maturity.
Your task is to create a comprehensive maturity assessment across multiple dimensions with cross-scoring analysis.

Focus on:
1. Multi-dimensional maturity assessment
2. Cross-functional maturity analysis
3. Benchmarking against industry standards
4. Maturity progression recommendations
5. Strategic maturity implications


ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE.
'''

user = '''
Analyze the following questions and answers to create a comprehensive maturity scoring:

Questions: {questions}
Answers: {answers}

Create maturity scoring analysis and return it in the following JSON format:
{{
    "maturityScoring": {{
        "dimensions": [
            {{
                "name": "Process Maturity",
                "score": 3.8,
                "level": "Managed",
                "subDimensions": [
                    {{
                        "name": "Standardization",
                        "score": 4.2,
                        "description": "Well-standardized processes across most areas"
                    }},
                    {{
                        "name": "Automation",
                        "score": 3.4,
                        "description": "Moderate automation with room for improvement"
                    }}
                ],
                "benchmark": 3.5,
                "gap": 0.3
            }}
        ],
        "crossScoring": {{
            "correlations": [
                {{
                    "dimension1": "Process Maturity",
                    "dimension2": "Technology Maturity",
                    "correlation": 0.75,
                    "impact": "strong positive"
                }}
            ],
            "synergies": [
                {{
                    "combination": "Process + Technology",
                    "synergyScore": 8.5,
                    "description": "Strong synergy between process and technology maturity"
                }}
            ]
        }},
        "overallMaturity": 4.1,
        "maturityLevel": "Managed",
        "progressionPath": [
            {{
                "nextLevel": "Optimized",
                "requirements": ["Advanced analytics", "Continuous improvement"],
                "timeline": "12-18 months",
                "investment": "medium"
            }}
        ],
        "industryBenchmark": {{
            "average": 3.8,
            "percentile": 65,
            "comparison": "above average"
        }}
    }}
}}

Guidelines:
- Assess maturity across 4-6 key dimensions
- Use 1-5 maturity scale with descriptive levels
- Include sub-dimensions for detailed analysis
- Calculate cross-dimensional correlations and synergies
- Provide progression path to next maturity level
- Benchmark against industry standards
- Identify key requirements for advancement
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''
