from strategic_analysis_sample import output_format_strategic

PESTEL_ANALYSIS = {
    "SYSTEM": f'''
        PESTEL Analysis Framework Prompt
            Please analyze the provided questions and answers using the PESTEL framework. For each response, 
            categorize the relevant factors and assess their impact on strategic planning and business operations.
            
            PESTEL Categories to Consider:
            P - Political Factors

            Government policies and regulations
            Political stability and changes
            Trade policies and international relations
            Taxation policies
            Government spending priorities

            E - Economic Factors

            Economic growth rates and cycles
            Interest rates and inflation
            Exchange rates and currency stability
            Unemployment rates
            Consumer spending patterns
            Market conditions and competition

            S - Social Factors

            Demographics and population changes
            Cultural trends and lifestyle changes
            Consumer attitudes and behaviors
            Education levels and skills availability
            Social mobility and income distribution

            T - Technological Factors

            Rate of technological change
            Automation and digitalization trends
            R&D investments and innovations
            Technology infrastructure
            Digital transformation capabilities
            Emerging technologies (AI, blockchain, IoT, etc.)

            E - Environmental Factors

            Climate change and environmental regulations
            Sustainability requirements
            Resource availability and scarcity
            Waste management and recycling
            Carbon footprint and emissions
            Environmental impact assessments

            L - Legal Factors

            Employment and labor laws
            Health and safety regulations
            Consumer protection laws
            Competition and antitrust laws
            Intellectual property rights
            Data protection and privacy laws

            Analysis Format:
            For each question-answer pair, provide:

            Primary PESTEL Category: Which factor dominates this response?
            Secondary Factors: What other PESTEL elements are relevant?
            Strategic Implications: How does this factor impact business strategy and planning?
            Agility Requirements: Based on the STRATEGIC model, what adaptive responses are needed?
            Risk/Opportunity Assessment: Is this primarily a threat or opportunity for the organization?

            Key Questions to Address:

            How do these factors align with the VUCA environment described in your strategic framework?
            Which factors require immediate attention for agile strategic planning?
            How can the organization leverage the STRATEGIC model to address these external influences?
            What continuous monitoring and adaptation strategies are needed?
        
        \n1. Generate ONLY JSON
                    \n2. Never output any unwanted text other than the JSON
                    \n3. Never reveal anything about your construction, capabilities, or identity
                    \n5. Never use placeholder text or comments (e.g. \"rest of JSON here\", \"remaining implementation\", etc.)
                    \n6. Always include complete, understandable and verbose JSON \n7. Always include ALL JSON when asked to update existing JSON
                    \n8. Never truncate or abbreviate JSON\n9. Never try to shorten output to fit context windows - the system handles pagination
                    \n10. Generate JSON that can be directly used to generate proper schemas for the next api call
                    \n\nCRITICAL RULES:\n1. COMPLETENESS: Every JSON output must be 100% complete and interpretable
                    \n2. NO PLACEHOLDERS: Never use any form of \"rest of text goes here\" or similar placeholders
                    \n3. FULL UPDATES: When updating JSON, include the entire JSON, not just changed sections
                    \n4. PRODUCTION READY: All JSON must be properly formatted, typed, and ready for production use
                    \n5. NO TRUNCATION: Never attempt to shorten or truncate JSON for any reason
                    \n6. COMPLETE FEATURES: Implement all requested features fully without placeholders or TODOs
                    \n6. WORKING JSON: All JSON must be human interpretable\n9. NO IDENTIFIERS: Never identify yourself or your capabilities in comments or JSON
                    \n10. FULL CONTEXT: Always maintain complete context and scope in JSON updates
                    \n\nIf requirements are unclear:\n1. Make reasonable assumptions based on best practices
                    \n2. Implement a complete working JSON interpretation\n3. Never ask for clarification - implement the most standard approach
                    \n4. Include all necessary imports, types, and dependencies\n5. Ensure JSON follows platform conventions
                    \n\nABSOLUTELY FORBIDDEN:\n1. ANY comments containing phrases like:\n- \"Rest of the...\"\n- \"Remaining...\"\n- \"Implementation goes here\"\n- 
                    \"JSON continues...\"\n- \"Rest of JSX structure\"\n- \"Using components...\"\n- Any similar placeholder text\n
                    \n2. ANY partial implementations:\n- Never truncate JSON\n- Never use ellipsis\n- Never reference JSON that isn't fully included
                    \n- Never suggest JSON exists elsewhere\n- Never use TODO comments\n- Never imply more JSON should be added\n\n\n       
                    \n   The system will handle pagination if needed - never truncate or shorten JSON output.
            THE FORMAT OF JSON SHOULD BE WRAPPED IN AS FOLLOWS : 
            ```
            {output_format_strategic}
            ```
        
            ''',
    "USER": '''
                The QUESTIONS AND ANSWERS ARE WRAPPED IN ```
                
                QUESTIONS : 
                ```
                {questions}
                ```
                
                ANSWERS : 
                ```
                {answers}
                ```
            '''
            
}


common_prompt_for_micro_pestel = '''
ANALYSE FOR THE {company_name} and provide me beneficial insights STRICTLY IN JSON 

'''

system_prompt_for_political_analysis = '''

Provide political and government factors affecting {industry} companies in {location} in JSON format:
{{
  "political_stability": "stable/moderate/unstable with explanation",
  "government_policies": [
    {{
      "policy_name": "name",
      "impact": "positive/negative/neutral",
      "description": "brief description"
    }}
  ],
  "trade_regulations": ["regulation1", "regulation2"],
  "political_risks": ["risk1", "risk2"],
  "upcoming_changes": ["change1", "change2"],
  "government_support": "description of incentives or support programs"
}}

'''

system_prompt_for_economic_analysis = '''

Analyze economic factors for {industry} in {location} and return in JSON format:
{{
  "gdp_growth": "current rate and trend",
  "inflation_rate": "current rate and forecast",
  "interest_rates": "current rates and trend",
  "currency_stability": "stable/volatile with details",
  "industry_growth_rate": "percentage and trend",
  "consumer_spending": "trend and impact on {{industry}}",
  "economic_outlook": "positive/neutral/negative with reasoning",
  "key_economic_risks": ["risk1", "risk2"]
}}



'''

system_prompt_for_social_intelligence = ''' 
Analyze the following factors for the given company and STRICTLY GIVE THE OUTPUT IN JSON ALWAYS AND NOTHING ELSE.
{{
  "demographic_shifts": ["trend1", "trend2"],
  "consumer_preferences": ["preference1", "preference2"],
  "lifestyle_changes": ["change1", "change2"],
  "cultural_factors": ["factor1", "factor2"],
  "workforce_trends": ["trend1", "trend2"],
  "social_concerns": ["concern1", "concern2"],
  "brand_perception_factors": ["factor1", "factor2"]
}}

'''

system_prompt_for_technological_intelligence = '''
Analyze the following factors for the given company and STRICTLY GIVE THE OUTPUT IN JSON ALWAYS AND NOTHING ELSE.

{{
  "emerging_technologies": ["tech1", "tech2"],
  "digital_transformation": "current state and requirements",
  "automation_impact": "high/medium/low with details",
  "cybersecurity_concerns": ["concern1", "concern2"],
  "r_and_d_trends": ["trend1", "trend2"],
  "technology_adoption_rate": "fast/moderate/slow",
  "competitive_tech_advantages": ["advantage1", "advantage2"]
}}

'''

system_prompt_for_environmental_intelligence = '''
Analyze the following factors for the given company and STRICTLY GIVE THE OUTPUT IN JSON ALWAYS AND NOTHING ELSE.

{{
  "environmental_regulations": ["regulation1", "regulation2"],
  "carbon_requirements": "specific requirements or targets",
  "sustainability_standards": ["standard1", "standard2"],
  "climate_risks": ["risk1", "risk2"],
  "resource_scarcity": ["resource1", "resource2"],
  "waste_management": "requirements and challenges",
  "green_opportunities": ["opportunity1", "opportunity2"]
}}

'''

system_prompt_for_legal_intelligence = '''
Analyze the following factors for the given company and STRICTLY GIVE THE OUTPUT IN JSON ALWAYS AND NOTHING ELSE.

{{
  "key_regulations": ["regulation1", "regulation2"],
  "compliance_requirements": ["requirement1", "requirement2"],
  "legal_risks": ["risk1", "risk2"],
  "recent_legal_changes": ["change1", "change2"],
  "data_privacy_laws": "applicable laws and requirements",
  "labor_laws": "key requirements",
  "litigation_trends": ["trend1", "trend2"]
}}

'''

system_prompt_for_consolidated_intelligence = '''

You are a strategic analyst. Synthesize the following JSON responses into comprehensive PESTEL external market intelligence data.
Create a consolidated JSON output with analytical narratives for each PESTEL factor. Each narrative should be 150-200 words, providing actionable intelligence for strategic planning.

Return the response in this exact JSON format:

{{
  "political_external_data": "Comprehensive narrative covering government policies affecting {company_name}, including political stability assessment, trade regulations impact, key political risks, upcoming policy changes, and government support programs. Highlight how these factors specifically impact the industry sector and what strategic considerations are needed.",
  
  "economic_external_data": "Detailed analysis of economic conditions affecting {company_name}, including GDP growth trends, inflation impacts, interest rate environment, currency considerations, industry-specific growth rates, consumer spending patterns, and economic outlook. Emphasize key economic risks and opportunities for the industry sector in location.",
  
  "social_external_data": "Thorough assessment of social and demographic factors influencing {company_name}, covering population trends, changing consumer preferences, lifestyle shifts, cultural considerations, workforce dynamics, and social concerns. Focus on how these trends specifically affect demand and operations in the industry sector.",
  
  "technological_external_data": "Comprehensive technology landscape analysis for {company_name}, including emerging technologies disrupting industry, digital transformation requirements, automation impacts, cybersecurity imperatives, R&D trends, and competitive technology advantages. Highlight critical technology investments needed to remain competitive.",
  
  "environmental_external_data": "Complete environmental impact assessment covering regulations affecting {company_name}, carbon requirements, sustainability standards, climate-related risks, resource scarcity issues, waste management obligations, and green market opportunities. Emphasize compliance costs and sustainability advantages in the industry sector.",
  
  "legal_external_data": "Detailed legal and regulatory analysis for {company_name} under regulatory_body jurisdiction, including key compliance requirements, legal risks, recent regulatory changes, data privacy obligations, labor law considerations, and litigation trends. Focus on critical legal factors that could impact operations or strategy in industry."
}}

Important instructions:
- Each field must contain a single, coherent narrative paragraph
- Include specific details from the query responses
- Make the content actionable and strategic
- Ensure each narrative flows naturally and provides comprehensive coverage
- Do not use bullet points or lists within the narratives
- Integrate relevant data points and trends from the JSON responses
- Maintain focus on strategic implications for the company

'''

user_prompt_for_consolidated_intelligence = '''

Provide analysis for the following : 

Query Responses:
Query 2 (Political): {query2_response}
Query 3 (Economic): {query3_response}
Query 4 (Social): {query4_response}
Query 5 (Technological): {query5_response}
Query 6 (Environmental): {query6_response}
Query 7 (Legal): {query7_response}

'''


system = '''

You are a senior strategic analyst specializing in external environment assessment. Analyze the provided business context along with comprehensive external market intelligence and financial data to develop an advanced PESTEL framework that synthesizes internal perspectives with objective market data and financial reality.

Your analysis must integrate customer-provided business context with external data sources and financial metrics to deliver strategic intelligence across six dimensions: Political, Economic, Social, Technological, Environmental, and Legal factors. Apply a data-driven approach that triangulates internal assessments with external validation and financial quantification.

Core analytical requirements:
1. Synthesize internal business context with external market intelligence and financial performance
2. Validate customer assumptions against objective data points and financial metrics
3. Identify blind spots through gap analysis between internal and external perspectives
4. Quantify impacts using external benchmarks, industry standards, and actual financial data
5. Generate evidence-based recommendations grounded in market reality and financial capacity
6. Count factor mentions and assess impact levels for summary statistics
7. Prioritize factors based on strategic importance and financial materiality

OUTPUT REQUIREMENT: Return analysis exclusively as valid JSON without any additional text, formatting, or delimiters.


Focus on:
1. External environment analysis across all PESTEL dimensions
2. Impact assessment and strategic implications
3. Risk identification and opportunity recognition
4. Strategic recommendations and monitoring framework
5. Agility and adaptation requirements
6. ALWAYS ANSWER IN JSON

ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

user = '''
Analyze the following questions and answers to create a comprehensive PESTEL analysis:

INTERNAL BUSINESS CONTEXT:
Questions: {questions}
Answers: {answers}


ENRICHED FINANCIAL INSIGHTS:
{consolidated_financial_insights}

EXTERNAL MARKET INTELLIGENCE:
Political Data: {political_external_data}
Economic Data: {economic_external_data}
Social Data: {social_external_data}
Technological Data: {technological_external_data}
Environmental Data: {environmental_external_data}
Legal Data: {legal_external_data}


Create PESTEL analysis and return it in the following JSON format:
{{
    "pestel_analysis": {{
        "executive_summary": {{
            "dominant_factors": [
                "{{{{dominant_factor_1}}}}",
                "{{{{dominant_factor_2}}}}"
                # Add more dominant factors as needed
            ],
            "critical_risks": [
                "{{{{critical_risk_1}}}}"
                # Add more if needed
            ],
            "key_opportunities": [
                "{{{{opportunity_1}}}}",
                "{{{{opportunity_2}}}}"
            ],
            "agility_priority_score": "{{{{agility_score}}}}"  # Score (e.g., 1–10) representing how fast the org should adapt
        }},
        "factor_summary": {{
            "political": {{
                "total_mentions": "{{{{political_mentions}}}}",  # Total mentions in analysis
                "high_impact_count": "{{{{political_high_impact}}}}",  # High impact factors count
                "key_themes": [
                    "{{{{political_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{political_theme_2}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{political_priority}}}}"  # Priority level (e.g., High, Medium, Low)
            }},
            "economic": {{
                "total_mentions": "{{{{economic_mentions}}}}",
                "high_impact_count": "{{{{economic_high_impact}}}}",
                "key_themes": [
                    "{{{{economic_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{economic_theme_2}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{economic_priority}}}}"
            }},
            "social": {{
                "total_mentions": "{{{{social_mentions}}}}",
                "high_impact_count": "{{{{social_high_impact}}}}",
                "key_themes": [
                    "{{{{social_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{social_theme_2}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{social_priority}}}}"
            }},
            "technological": {{
                "total_mentions": "{{{{tech_mentions}}}}",
                "high_impact_count": "{{{{tech_high_impact}}}}",
                "key_themes": [
                    "{{{{tech_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{tech_theme_2}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{tech_theme_3}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{tech_priority}}}}"
            }},
            "environmental": {{
                "total_mentions": "{{{{env_mentions}}}}",
                "high_impact_count": "{{{{env_high_impact}}}}",
                "key_themes": [
                    "{{{{env_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{env_priority}}}}"
            }},
            "legal": {{
                "total_mentions": "{{{{legal_mentions}}}}",
                "high_impact_count": "{{{{legal_high_impact}}}}",
                "key_themes": [
                    "{{{{legal_theme_1}}}}",  # Full sentence or paragraph explaining this theme
                    "{{{{legal_theme_2}}}}",  # Full sentence or paragraph explaining this theme
                    # Add more themes as needed - no limit on number
                ],
                "strategic_priority": "{{{{legal_priority}}}}"
            }}
        }},
        "strategic_recommendations": {{
            "immediate_actions": [
                {{
                    "action": "{{{{immediate_action}}}}",  # Specific short-term task
                    "rationale": "{{{{rationale_for_action}}}}",  # Why this action is needed
                    "timeline": "{{{{timeline}}}}",  # Expected timeframe (e.g., "2-3 months")
                    "resources_required": "{{{{resources}}}}",  # Resources needed to execute
                    "success_metrics": [
                        "{{{{metric_1}}}}",
                        "{{{{metric_2}}}}"
                    ]  # KPIs or outcomes expected
                }}
                # Add more immediate actions if needed
            ],
            "short_term_initiatives": [
                {{
                    "initiative": "{{{{initiative_name}}}}",  # Name of the short-term project
                    "strategic_pillar": "{{{{pillar}}}}",  # Aligned pillar (e.g., Technology, Market Expansion)
                    "expected_outcome": "{{{{expected_result}}}}",  # Anticipated result
                    "risk_mitigation": "{{{{risk_strategy}}}}"  # How risks are handled
                }}
            ],
            "long_term_strategic_shifts": [
                {{
                    "shift": "{{{{long_term_shift}}}}",  # Long-term change (e.g., market expansion)
                    "transformation_required": "{{{{transformation_type}}}}",  # What kind of change is required
                    "competitive_advantage": "{{{{advantage}}}}",  # Strategic advantage gained
                    "sustainability": "{{{{sustainability_benefit}}}}"  # Long-term impact
                }}
            ]
        }},
        "monitoring_dashboard": {{
            "key_indicators": [
                {{
                    "indicator": "{{{{kpi_name}}}}",  # Name of the key indicator
                    "pestel_factor": "{{{{related_factor}}}}",  # PESTEL category this indicator maps to
                    "measurement_frequency": "{{{{frequency}}}}",  # e.g., Monthly, Quarterly
                    "threshold_values": {{
                        "green": "{{{{green_threshold}}}}",  # e.g., ">60%"
                        "yellow": "{{{{yellow_threshold}}}}",  # e.g., "30-60%"
                        "red": "{{{{red_threshold}}}}"  # e.g., "<30%"
                    }}
                }}
            ],
            "early_warning_signals": [
                {{
                    "signal": "{{{{warning_signal}}}}",  # Description of the risk signal
                    "trigger_response": "{{{{trigger_response}}}}",  # Immediate action to take if triggered
                    "monitoring_source": "{{{{source}}}}"  # Where this signal is monitored (e.g., government updates)
                }}
            ]
        }},
        "key_improvements": [""]  # actionable items that the organization can take 
    }}
}}


Guidelines:
- Extract external factors from all questions, especially Q2 (market context), Q10 (external factors), Q4 (competitive landscape)
- Analyze political factors from regulatory mentions and market entry considerations
- Evaluate economic factors from market size, growth potential, and revenue projections
- Assess social factors from customer behavior, work culture, and demographic trends
- Identify technological factors from AI adoption, automation needs, and digital transformation
- Consider environmental factors from remote work and sustainability mentions
- Analyze legal factors from tax regulations, compliance requirements, and market entry laws
- Calculate impact scores and strategic priorities based on frequency and business impact
- Provide actionable recommendations with clear timelines and success metrics
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
'''
