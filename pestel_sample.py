pestel_analysis_template = {
    "pestel_analysis": {
        # High-level summary of findings from the PESTEL analysis
        "executive_summary": {
            "dominant_factors": [],  # Top external factors influencing the business
            "critical_risks": [],  # Most significant threats identified
            "key_opportunities": [],  # Main opportunities available
            "strategic_recommendations": [],  # High-level strategic suggestions
            "agility_priority_score": 0  # Score (0–10) indicating urgency of agile adaptation
        },

        # Summary of each PESTEL factor with counts and priorities
        "factor_summary": {
            "political": {
                "total_mentions": 0,  # How many times political factors appeared
                "high_impact_count": 0,  # Count of high-impact political factors
                "key_themes": [],  # Main political themes affecting strategy
                "strategic_priority": "High|Medium|Low"  # Priority level
            },
            "economic": {
                "total_mentions": 0,
                "high_impact_count": 0,
                "key_themes": [],
                "strategic_priority": "High|Medium|Low"
            },
            "social": {
                "total_mentions": 0,
                "high_impact_count": 0,
                "key_themes": [],
                "strategic_priority": "High|Medium|Low"
            },
            "technological": {
                "total_mentions": 0,
                "high_impact_count": 0,
                "key_themes": [],
                "strategic_priority": "High|Medium|Low"
            },
            "environmental": {
                "total_mentions": 0,
                "high_impact_count": 0,
                "key_themes": [],
                "strategic_priority": "High|Medium|Low"
            },
            "legal": {
                "total_mentions": 0,
                "high_impact_count": 0,
                "key_themes": [],
                "strategic_priority": "High|Medium|Low"
            }
        },

        # Detailed recommendations grouped by urgency
        "strategic_recommendations": {
            "immediate_actions": [
                {
                    "action": "Specific action item",  # The exact action to take
                    "rationale": "Why this action is needed",  # Reason for the action
                    "timeline": "Implementation timeline",  # e.g., "2 weeks", "Q1 2025"
                    "resources_required": "Resource requirements",  # People, tools, money
                    "success_metrics": ["Metric 1", "Metric 2"]  # How to measure success
                }
            ],
            "short_term_initiatives": [
                {
                    "initiative": "Initiative description",  # Short-term project
                    "strategic_pillar": "Which STRATEGIC model pillar this addresses",  
                    "expected_outcome": "Expected result",  
                    "risk_mitigation": "How this addresses identified risks"
                }
            ],
            "long_term_strategic_shifts": [
                {
                    "shift": "Strategic shift description",  # Big transformation idea
                    "transformation_required": "What needs to change",  
                    "competitive_advantage": "How this creates advantage",  
                    "sustainability": "Long-term viability"
                }
            ]
        },

        # Dashboard for ongoing tracking
        "monitoring_dashboard": {
            "key_indicators": [
                {
                    "indicator": "Specific metric to track",  # KPI name
                    "pestel_factor": "Related PESTEL category",  
                    "measurement_frequency": "How often to measure",  # e.g., "Monthly"
                    "threshold_values": {
                        "green": "Safe zone values",  
                        "yellow": "Caution zone values", 
                        "red": "Critical zone values"
                    }
                }
            ],
            "early_warning_signals": [
                {
                    "signal": "What to watch for",  # Trigger event
                    "trigger_response": "What action to take when detected",  
                    "monitoring_source": "Where to get this information"  # Data source
                }
            ]
        }
    }
}
