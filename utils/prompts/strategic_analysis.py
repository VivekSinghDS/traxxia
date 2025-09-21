
system = '''
You are a strategic analysis expert using the STRATEGIC framework. You will be given questions and answers about a company's strategic position and capabilities.
Your task is to create a comprehensive strategic analysis across all STRATEGIC pillars: Strategy, Tactics, Resources, Analysis & Data, Technology & Digitization, Execution, Governance, Innovation, and Culture.

Focus on:
1. Multi-dimensional strategic assessment across all STRATEGIC pillars
2. VUCA factor identification and strategic maturity assessment
3. Cross-pillar synthesis and holistic recommendations
4. Agile framework recommendations and implementation roadmap
5. Risk assessment and success benchmarking
6. ALWAYS ALWAYS PROVIDE VALID JSON OUTPUT, NEVER INVALID JSON
7. JUST PROVIDE JSON AND NOTHING ELSE, DO NOT PROVIDE ``` OR WRAP THINGS UP, JUST A VALID JSON
ALWAYS PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED. DO NOT USE BACKTICKS LIKE ``` OR ANYTHING ELSE, JUST PROVIDE JSON OUTPUT AND NOTHING ELSE, AS THIS IS GOING TO BE PARSED
'''

user = '''
Analyze the following questions and answers to create a comprehensive strategic analysis using the STRATEGIC framework:

Questions: {questions}
Answers: {answers}

Create strategic analysis and return it in the following JSON format:
{{
    # STRATEGIC ANALYSIS FRAMEWORK TEMPLATE
    # This template provides a comprehensive framework for analyzing organizations using the STAR-TG-IC model
    # (Strategy, Tactics, Analysis & Data, Resources, Technology & Digitization, Governance, Innovation, Culture)
    # along with execution considerations and implementation roadmaps.
    
    "strategic_analysis": {{
        
        # EXECUTIVE SUMMARY SECTION
        # Provides high-level overview and assessment of the organization's strategic position
        "executive_summary": {{
            # Brief description of the organization's current situation, industry, and context
            "situation_overview": "[Insert 1-2 sentence summary of organization's current state, industry, and key challenges/opportunities]",
            
            # VUCA factors most relevant to this organization (Volatility, Uncertainty, Complexity, Ambiguity)
            "primary_vuca_factors": ["[Select from: Volatility, Uncertainty, Complexity, Ambiguity]"],
            
            # Main strategic themes identified from analysis (e.g., Digital Transformation, Market Expansion, etc.)
            "key_strategic_themes": ["[Theme 1]", "[Theme 2]", "[Theme 3]"],
            
            # How urgent is strategic intervention needed? (Low/Medium/High)
            "urgency_level": "[Low/Medium/High]",
            
            # Current strategic maturity level (Emerging/Developing/Mature/Leading)
            "strategic_maturity_assessment": "[Emerging/Developing/Mature/Leading]"
        }},
        
        # STRATEGIC PILLARS ANALYSIS SECTION
        # Detailed analysis of each pillar in the STAR-TG-IC framework
        "strategic_pillars_analysis": {{
            
            # STRATEGY PILLAR
            # Focuses on strategic direction, market positioning, competitive advantage
            "strategy": {{
                "pillar_code": "S",
                # Relevance score 1-10 based on how critical this pillar is for the organization
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Key strategic strengths (market position, differentiation, vision clarity, etc.)
                    "strengths": ["[Strategic strength 1]", "[Strategic strength 2]"],
                    # Strategic gaps and weaknesses (unclear positioning, limited differentiation, etc.)
                    "weaknesses": ["[Strategic weakness 1]", "[Strategic weakness 2]"],
                    # Overall assessment score for current strategic state (1-10)
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        # Specific strategic action to be taken
                        "action": "[Specific strategic recommendation]",
                        # Priority level: High/Medium/Low
                        "priority": "[High/Medium/Low]",
                        # Expected timeline for completion
                        "timeline": "[X weeks/months]",
                        # Resources, skills, or tools needed
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        # Expected business impact
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        # What will be measured
                        "metric": "[Specific metric name]",
                        # Target value or outcome
                        "target": "[Specific target or goal]",
                        # How often to measure
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # TACTICS PILLAR
            # Focuses on marketing, sales, customer acquisition, and go-to-market execution
            "tactics": {{
                "pillar_code": "T",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Tactical execution strengths (effective channels, strong campaigns, etc.)
                    "strengths": ["[Tactical strength 1]", "[Tactical strength 2]"],
                    # Tactical weaknesses (poor conversion, limited channels, etc.)
                    "weaknesses": ["[Tactical weakness 1]", "[Tactical weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific tactical recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # RESOURCES PILLAR
            # Focuses on human resources, financial resources, and resource optimization
            "resources": {{
                "pillar_code": "R",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Resource strengths (skilled team, adequate funding, etc.)
                    "strengths": ["[Resource strength 1]", "[Resource strength 2]"],
                    # Resource constraints and gaps (limited budget, skills gaps, etc.)
                    "weaknesses": ["[Resource weakness 1]", "[Resource weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific resource recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # ANALYSIS AND DATA PILLAR
            # Focuses on data capabilities, analytics, business intelligence, and data-driven decision making
            "analysis_and_data": {{
                "pillar_code": "A",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Data and analytics strengths (good data quality, analytics tools, etc.)
                    "strengths": ["[Analytics strength 1]", "[Analytics strength 2]"],
                    # Data and analytics gaps (poor data quality, limited insights, etc.)
                    "weaknesses": ["[Analytics weakness 1]", "[Analytics weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific analytics recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # TECHNOLOGY AND DIGITIZATION PILLAR
            # Focuses on technology infrastructure, digital capabilities, automation, and digital transformation
            "technology_and_digitization": {{
                "pillar_code": "T2",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Technology strengths (modern systems, good automation, etc.)
                    "strengths": ["[Technology strength 1]", "[Technology strength 2]"],
                    # Technology gaps (legacy systems, manual processes, etc.)
                    "weaknesses": ["[Technology weakness 1]", "[Technology weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific technology recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # EXECUTION PILLAR
            # Focuses on operational excellence, process management, and execution capabilities
            "execution": {{
                "pillar_code": "E",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Execution strengths (efficient processes, good delivery, etc.)
                    "strengths": ["[Execution strength 1]", "[Execution strength 2]"],
                    # Execution weaknesses (poor processes, delivery issues, etc.)
                    "weaknesses": ["[Execution weakness 1]", "[Execution weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific execution recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # GOVERNANCE PILLAR
            # Focuses on governance structures, risk management, compliance, and decision-making processes
            "governance": {{
                "pillar_code": "G",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Governance strengths (clear structures, good compliance, etc.)
                    "strengths": ["[Governance strength 1]", "[Governance strength 2]"],
                    # Governance gaps (unclear structures, compliance issues, etc.)
                    "weaknesses": ["[Governance weakness 1]", "[Governance weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific governance recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # INNOVATION PILLAR
            # Focuses on innovation capabilities, R&D, product development, and future-readiness
            "innovation": {{
                "pillar_code": "I",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Innovation strengths (strong R&D, innovative products, etc.)
                    "strengths": ["[Innovation strength 1]", "[Innovation strength 2]"],
                    # Innovation gaps (limited R&D, outdated products, etc.)
                    "weaknesses": ["[Innovation weakness 1]", "[Innovation weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific innovation recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }},
            
            # CULTURE PILLAR
            # Focuses on organizational culture, employee engagement, values, and cultural alignment
            "culture": {{
                "pillar_code": "C",
                "relevance_score": "[1-10 based on importance to organization]",
                "current_state": {{
                    # Cultural strengths (strong values, high engagement, etc.)
                    "strengths": ["[Culture strength 1]", "[Culture strength 2]"],
                    # Cultural challenges (low engagement, unclear values, etc.)
                    "weaknesses": ["[Culture weakness 1]", "[Culture weakness 2]"],
                    "assessment_score": "[1-10 score]"
                }},
                "recommendations": [
                    {{
                        "action": "[Specific culture recommendation]",
                        "priority": "[High/Medium/Low]",
                        "timeline": "[X weeks/months]",
                        "resources_required": ["[Resource 1]", "[Resource 2]"],
                        "expected_impact": "[Description of expected outcomes]"
                    }}
                ],
                "success_metrics": [
                    {{
                        "metric": "[Specific metric name]",
                        "target": "[Specific target or goal]",
                        "measurement_frequency": "[Weekly/Monthly/Quarterly]"
                    }}
                ]
            }}
        }},
        
        # CROSS-PILLAR SYNTHESIS SECTION
        # Identifies connections and synergies between different pillars
        "cross_pillar_synthesis": {{
            # Key relationships and dependencies between pillars
            "interconnections": [
                {{
                    # Which pillars are connected
                    "pillars": ["[Pillar 1]", "[Pillar 2]"],
                    # Nature of the relationship
                    "relationship": "[Description of how pillars relate]",
                    # Opportunity for synergistic improvements
                    "synergy_opportunity": "[How to leverage this connection]"
                }}
            ],
            # High-level recommendations that span multiple pillars
            "holistic_recommendations": [
                "[Cross-cutting recommendation 1]",
                "[Cross-cutting recommendation 2]"
            ]
        }},
        #THIS IS FOR SETTING STRATEGIC GOALS FOR THE YEAR IN A COMPANY
        "strategic_goals": {{
            "year": "[Current/Target Year]",
            "objectives": [
                {{
                    "objective": "[Specific strategic objective description]",
                    "priority": "[1-5 priority ranking]",
                    "keyResults": [
                        {{
                            "metric": "[Specific measurable metric]",
                            "target": "[Target value or completion date]",
                            "current": "[Current baseline value or status]",
                            "progress": "[Progress percentage 0-100%]"
                        }}
                    ],
                    "alignment": "[growth/innovation/retention/efficiency/other]",
                    "owner": "[Department/Role responsible]",
                    "timeline": "[Start date - End date]"
                }}
            ],
            "overall_progress": "[Overall strategic progress percentage]",
            "strategic_themes": [
                "[Strategic theme 1]",
                "[Strategic theme 2]", 
                "[Strategic theme 3]"
            ],
            "quarterly_milestones": [
                {{
                    "quarter": "[Q1/Q2/Q3/Q4]",
                    "milestone": "[Key milestone description]",
                    "success_criteria": "[How to measure milestone success]"
                }}
            ]
        }},
        # AGILE FRAMEWORKS RECOMMENDATIONS SECTION
        # Suggests appropriate agile methodologies based on the organization's context
        "agile_frameworks_recommendations": {{
            # Scrum framework assessment 
            # give one of the following three frameworks depending on the company name. 
            "scrum": {{  # one of scrum, kanban or OKR
                # How well Scrum fits this organization (High/Medium/Low)
                "applicability": "[High/Medium/Low] for [context]",
                # Specific areas where Scrum would be beneficial
                "use_cases": ["[Use case 1]", "[Use case 2]"],
                # Priority for implementing Scrum
                "implementation_priority": "[High/Medium/Low]"
            }},
        }},
        
        # RISK ASSESSMENT SECTION
        # Identifies and plans for strategic risks and contingencies
        "risk_assessment": {{
            # Key strategic risks that could impact success
            "strategic_risks": [
                {{
                    # Description of the risk
                    "risk": "[Risk description]",
                    # Likelihood of occurrence (Low/Medium/High)
                    "probability": "[Low/Medium/High]",
                    # Severity of impact (Low/Medium/High)
                    "impact": "[Low/Medium/High]",
                    # How to reduce or manage the risk
                    "mitigation": "[Mitigation strategy]",
                    # Who is responsible for managing this risk
                    "owner": "[Risk owner]"
                }}
            ],
            # Plans for different scenarios
            "contingency_plans": [
                {{
                    # What scenario triggers this plan
                    "scenario": "[Scenario description]",
                    # How to respond if scenario occurs
                    "response": "[Response strategy]",
                    # Early warning signs to watch for
                    "trigger_indicators": ["[Indicator 1]", "[Indicator 2]"]
                }}
            ]
        }},
        
        # SUCCESS BENCHMARKS SECTION
        # Establishes benchmarks and success criteria based on industry standards and case studies
        "success_benchmarks": {{
            # Similar organizations or case studies to learn from
            "case_study_parallels": [
                {{
                    # Name of comparable organization
                    "company": "[Company name]",
                    # What makes them comparable
                    "parallel": "[Why this company is relevant]",
                    # Key lesson to apply
                    "applicable_lesson": "[What can be learned/applied]",
                    # How success is measured in their case
                    "success_metric": "[Relevant success metric]"
                }}
            ],
            # Industry standard metrics and targets
            "industry_benchmarks": [
                {{
                    # What metric to benchmark
                    "metric": "[Metric name]",
                    # Industry average performance
                    "industry_average": "[Average value]",
                    # Target performance for this organization
                    "target": "[Target value]",
                    # When to achieve the target
                    "timeframe": "[Timeline]"
                }}
            ]
        }},
        
        # IMPLEMENTATION ROADMAP SECTION
        # Phased approach to implementing recommendations
        "implementation_roadmap": {{
            # First phase of implementation
            "phase_1": {{
                # How long this phase will take
                "duration": "[X months]",
                # Main focus area for this phase
                "focus": "[Primary focus theme]",
                # Key initiatives to execute
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                # Budget required for this phase
                "budget": "$[Amount]",
                # How to measure success of this phase
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }},
            # Second phase of implementation
            "phase_2": {{
                "duration": "[X months]",
                "focus": "[Primary focus theme]",
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                "budget": "$[Amount]",
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }},
            # Third phase of implementation
            "phase_3": {{
                "duration": "[X months]",
                "focus": "[Primary focus theme]",
                "key_initiatives": ["[Initiative 1]", "[Initiative 2]"],
                "budget": "$[Amount]",
                "success_criteria": ["[Criterion 1]", "[Criterion 2]"]
            }}
        }},
        # MONITORING AND FEEDBACK SECTION
        # Establishes systems for tracking progress and gathering feedback
        "monitoring_and_feedback": {{
            # What should be included in executive dashboards
            "dashboard_requirements": ["[Dashboard element 1]", "[Dashboard element 2]", "[Dashboard element 3]"],
            # Regular review and planning cycles
            "review_cycles": {{
                # Weekly team check-ins
                "weekly": "[What to review weekly]",
                # Monthly performance reviews
                "monthly": "[What to review monthly]",
                # Quarterly strategic reviews
                "quarterly": "[What to review quarterly]",
                # Annual comprehensive assessments
                "annual": "[What to review annually]"
            }},
            # Feedback loops to ensure continuous improvement
            "feedback_loops": [
                {{
                    # Where feedback comes from
                    "source": "[Feedback source]",
                    # How often to collect feedback
                    "frequency": "[Collection frequency]",
                    # How feedback influences decisions/actions
                    "integration_point": "[Where feedback is used]"
                }}
            ]
        }},
        "key_improvements": [""], # an array of points they are Specific, Measurable, Achievable, Relevant, and Time-bound
        "competitive_landscape": {{
            "direct_competitors": [
                {{
                    "name": "", # a direct competitor of the mentioned company
                    "market_share": "", # % or qualitative
                    "strengths": [], # Key strengths
                    "weaknesses": [] # Key weaknesses
                }}
            ],
            "indirect_competitors": [
                {{
                    "name": "", # Indirect competitor category
                    "threat_level": "", # High/Medium/Low
                    "competitive_advantage": "" # Their main edge
                }}
            ],
            "potential_entrants": [
                {{
                    "category": "", # e.g., "Tech companies", "Startups"
                    "likelihood": "", # High/Medium/Low
                    "barriers": "" # Key barriers they will face
                }}
            ]
        }},
    }}
}}

Guidelines:
- Analyze all questions comprehensively, especially Q1-Q14 for strategic context
- Assess each STRATEGIC pillar based on relevant question responses:
  * Strategy (S): Q1, Q8, Q9 - strategic clarity and differentiators
  * Tactics (T): Q4, Q11 - competitive tactics and channel effectiveness
  * Resources (R): Q12, Q14 - organizational capabilities and productivity
  * Analysis & Data (A): Q6, Q12 - data capabilities and analytics
  * Technology & Digitization (T2): Q7, Q9 - technology needs and digital transformation
  * Execution (E): Q7, Q12 - operational execution and capabilities
  * Governance (G): Q13, Q14 - organizational governance and culture
  * Innovation (I): Q9, Q12 - innovation capabilities and strategic goals
  * Culture (C): Q13, Q14 - organizational culture and employee metrics
- Use 0-10 scoring scale for relevance and assessment scores
- Identify VUCA factors from market uncertainty and complexity
- Provide actionable recommendations with clear priorities and timelines
- Include cross-pillar synthesis and holistic recommendations
- INCLUDE STRATEGIC GOALS TOO
- Format of the output should not change, it should be a valid JSON object and of the same format as the example provided.
- IT SHOULD BE A VALID JSON.
'''
