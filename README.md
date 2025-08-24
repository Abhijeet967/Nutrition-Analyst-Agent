# Nutrition-Analyst-Agent
A specialized nutrition and food analysis assistant agent that connects to the USDA Food Data Central MCP (Model Context Protocol) server. This agent is designed to help with meal planning, nutritional analysis, dietary guidance, and comprehensive food database queries for making informed food choices in daily life.

Capabilities
This agent can:

Search through 300,000+ foods in the USDA database
Provide detailed nutritional breakdowns including macros, vitamins, and minerals
Compare multiple foods side-by-side for informed decision making
Analyze meal compositions and calculate total nutritional values
Generate personalized dietary recommendations based on health goals
Filter foods by data source (Foundation, Branded, Survey, Legacy, Experimental)
Support special dietary needs (diabetes, heart health, weight management)
Offer food alternatives and healthier substitutions
Help with grocery shopping decisions and meal planning
Provide nutrient-specific analysis for targeted nutritional goals
Connected MCP Server
The agent connects to the following specialized nutrition server:

USDA Food Data Central MCP Server
Access to comprehensive USDA Food Data Central database with 300,000+ foods
Real-time nutritional data from official government sources
Multiple food data sources including branded products and research data
Available tools:

search_foods: Search foods by name with filtering options
get_food_details: Get comprehensive nutritional information for specific foods
get_food_nutrients: Get targeted nutrient information for foods
compare_foods: Side-by-side nutritional comparison of multiple foods
get_nutrient_reference: Reference guide for nutrient IDs and descriptions
get_data_types: Information about available food data sources
