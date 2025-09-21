system = '''
You are a maturity score analyst. You will be given questions and answers about a company's overall maturity across multiple dimensions.
Your task is to create a comprehensive maturity score analysis synthesizing indicators from all questions (Q1-Q14).

Focus on:
1. Cross-reference all assessments from Q1-Q14
2. Synthesize maturity indicators across dimensions
3. Calculate overall maturity score on 1-5 scale
4. Identify maturity profile and characteristics
5. Determine strengths, development areas, and next level requirements

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

user = '''
Analyze the following questions and answers to create maturity score (light) analysis:

Questions: {questions}
Answers: {answers}

Create maturity score analysis and return it in the following JSON format:
 {{
    "maturityScore": {{
        "overallScore": "{{overall_score}}",  # Overall maturity score (e.g., 3.2)
        "level": "{{maturity_level}}",  # Maturity level label (e.g., 'Defined', 'Managed')
        "components": {{
            "strategicClarity": "{{strategic_clarity}}",  # Score for strategic clarity
            "marketAlignment": "{{market_alignment}}",  # Score for alignment with market
            "customerFocus": "{{customer_focus}}",  # Score reflecting customer-centric practices
            "operationalCapability": "{{operational_capability}}",  # Score for operational strength
            "competitivePosition": "{{competitive_position}}",  # Score showing competitive differentiation
            "organizationalHealth": "{{organizational_health}}"  # Score for team/org health and sustainability
        }},
        "maturityProfile": "{{maturity_profile}}",  # Descriptive profile of current maturity (e.g., 'Customer-Led Growth')
        "strengths": [
            "{{strength_1}}",
            "{{strength_2}}",
            "{{strength_3}}"
            # Add more as needed
        ],
        "developmentAreas": [
            "{{development_area_1}}",
            "{{development_area_2}}",
            "{{development_area_3}}"
            # Add more if needed
        ],
        "nextLevel": {{
            "target": "{{next_maturity_level}}",  # Next maturity level (e.g., 'Managed (Level 4)')
            "requirements": [
                "{{requirement_1}}",
                "{{requirement_2}}",
                "{{requirement_3}}",
                "{{requirement_4}}"
                # Add or remove based on actual needs
            ],
            "estimatedTimeframe": "{{timeframe}}"  # Time estimate to reach next level (e.g., '12-18 months')
        }}
    }}
}}



Guidelines:
- Cross-reference all assessments from Q1-Q14 to synthesize maturity indicators
- Calculate component scores: Strategic Clarity (Q1, Q8, Q9), Market Alignment (Q2, Q4, Q10), Customer Focus (Q3, Q6, Q8, Q11), Operational Capability (Q7, Q12), Competitive Position (Q8), Organizational Health (Q13, Q14)
- Use 1-5 maturity scale: 1=Initial, 2=Developing, 3=Defined, 4=Managed, 5=Optimized
- Determine overall score as weighted average of components
- Identify maturity profile based on strongest characteristics
- List key strengths and development areas
- Define next level requirements and timeframe
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''
