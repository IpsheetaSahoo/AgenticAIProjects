"""
=========================================================================================
Agentic Business Strategy Planner with Society-of-Mind and Human-in-the-Loop Coordination
=========================================================================================

Description:
This project implements a multi-agent, human-in-the-loop business analyst 
pipeline using Microsoft AutoGen (stable release). It simulates a real-world 
strategic decision making system where multiple AI agents perform market, 
financial, and customer analysis, followed by human validation and  
presentation slide generation in json.


1. **Inner RoundRobin Team**:
   - MarketAnalystAgent
   - FinancialModelAgent
   - CustomerInsightAgent
   - UserProxyAgent_Inner (for human feedback)
   → Managed by a SocietyOfMindAgent (InnerTeamSoM)

2. **Outer Selector Team**:
   - RoutingAgent (controls overall flow)
   - InnerTeamSoM (analysis generator after inner team run)
   - UserProxyAgent_Outer (final human validation)
   - PPTExtractionAgent (creates structured JSON for a single-slide presentation)

3. **SelectorGroupChat Logic**:
   - Controlled by a custom selector function and prompt.
   - Enforces strict turn-taking: RoutingAgent → InnerTeamSoM → UserProxyAgent_Outer → PPTExtractionAgent → Feedback.

4. **Human-in-the-Loop**:
   - Approves or sends feedback at two stages: during inner team analysis and after synthesis review.

5. **Output**:
   - Final approved insights are converted into structured JSON.

"""



#Set Up Dependencies and Model
import asyncio
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import AssistantAgent,UserProxyAgent, SocietyOfMindAgent
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import TextMentionTermination  , MaxMessageTermination   
from typing import Sequence
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from dotenv import load_dotenv
import os              

    

# Load API key
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Model client
model_client = OpenAIChatCompletionClient(model='gpt-4o-mini', api_key=api_key)

#1. **Inner RoundRobin Team**:


#Initializes a MarketAnalystAgent that generates concise strategic insights on market trends, competitors, and growth opportunities
market_analyst_agent = AssistantAgent(
    name="MarketAnalystAgent",
    description="Analyzes market trends, industry shifts, and competitor strategies.",
    model_client=model_client,
    system_message="""
    You are a senior market research analyst.
    Your role is to identify key market trends, evaluate industry opportunities,
    and summarize competitor positioning for strategic decisions and generate output in format mentioned

    Tasks you handle:
    - Identifying growth sectors or declining trends
    - Comparing competitor strengths and weaknesses
    - Analyzing geographical or seasonal market factors

    Output Format:
    Create output in the following format where each section is a bullet point and not more than 1-2 sentences:
    - Key Insight 1: ...
    - Key Insight 2: ...
    - Recommendation: ...
    """
)

#Defines the FinancialModelAgent to assess financial viability, including costs, ROI, breakeven, and risk for business strategies using a bullet-format response.
financial_model_agent = AssistantAgent(
    name="FinancialModelAgent",
    description="Evaluates costs, profitability, and ROI for strategic plans.",
    model_client=model_client,
    system_message="""
    You are a financial strategist responsible for modeling and evaluating the financial viability
    of proposed business strategies and generate output in format mentioned.

    Your responsibilities include:
    - Cost estimation
    - ROI calculation
    - Breakeven analysis
    - Identifying financial risks

    Output Format:
    Create output in the following format where each section is a bullet point and not more than 1-2 sentences:
    - Estimated Cost: ...
    - Projected ROI: ...
    - Breakeven Point: ...
    - Financial Risks: ...
    """
)

#Defines the CustomerInsightAgent to analyze customer feedback, sentiment, and behavior to extract actionable insights in a bullet-point format.
customer_insight_agent = AssistantAgent(
    name="CustomerInsightAgent",
    description="Analyzes customer feedback, sentiment, and behavior to extract actionable insights.",
    model_client=model_client,
    system_message="""
    You are a customer experience analyst.
    Your job is to interpret customer feedback, behavior, and sentiment from surveys, reviews, and usage data and generate output in format mentioned.

    You focus on:
    - Detecting satisfaction or dissatisfaction patterns
    - Identifying common feature requests or complaints
    - Spotting churn risks or loyalty indicators

    Output Format:
    Create output in the following format where each section is a bullet point and not more than 1-2 sentences:
    - Customer Sentiment Summary: ...
    - Top Feedback Themes: ...
    - Recommended Actions: ...
    """
)

#Defines the UserProxyAgent_Inner to act as a human reviewer and decision maker for the inner team, collecting feedback via console input.
user_proxy_inner = UserProxyAgent(
    name="UserProxyAgent_Inner",
    description="Acts as the human reviewer and decision maker for the inner team.",
    input_func=input  # Uses console input to collect human feedback
)

inner_termination = TextMentionTermination("APPROVED")  # Termination condition: end inner team discussion when human types "APPROVED"

inner_agents = [
    market_analyst_agent,
    financial_model_agent,
    customer_insight_agent,
    user_proxy_inner  # Include the human-in-the-loop agent

]

#Defines the RoundRobinGroupChat for the inner team, allowing agents to take turns responding to tasks.
# The inner team will analyze market, financial, and customer data for strategic planning input.
inner_round_robin_team = RoundRobinGroupChat(
    participants=inner_agents,
    termination_condition=inner_termination
)


# 2. **Outer Selector Team**:

#Defines the SocietyOfMindAgent that coordinates the inner team, synthesizing their insights into a concise strategic analysis of the business task.
# It manages the round-robin process and synthesizes insights into a concise, factual strategic analysis
inner_som_agent = SocietyOfMindAgent(
    name="InnerTeamSoM",
    team=inner_round_robin_team,
    model_client=model_client,
    description="This inner team analyzes market, financial, and customer data for strategic planning input.",
    response_prompt='''
You are the InnerTeamSoM agent.

Your role is to:
- Coordinate with internal experts (MarketAnalystAgent, FinancialModelAgent, CustomerInsightAgent) via a round-robin process.
- Synthesize their insights into a concise, factual strategic analysis of the business task.

### Workflow Rules:
- You receive tasks and feedback **exclusively from the RoutingAgent**, not from the user or other agents directly.
- Once your synthesis is complete, respond back so the RoutingAgent can forward it for user approval.
- If you receive feedback from the RoutingAgent (originating from the user) asking for changes to your analysis:
  - Re-engage your internal team to improve the content based on the specific feedback.
- Do NOT handle or comment on presentation or slide formatting.
- Do NOT reroute tasks — your job is to analyze and revise, then output.

### Your Output Format:
Use bullet points — concise, clear, and factual:
- Key Insight 1: ...
- Key Insight 2: ...
- Recommendation: ...
'''
)

#Defines the RoutingAgent that manages the outer workflow, routing tasks to the correct agent based on user feedback and task progression.
# It initiates the process, routes tasks to InnerTeamSoM, PPTExtractionAgent and manages user feedback
routing_agent = AssistantAgent(
    name="RoutingAgent",
    description="An agent responsible for managing the outer workflow by routing tasks to the correct agent.",
    model_client=model_client,
    system_message="""
You are the RoutingAgent responsible for managing the outer business analysis workflow.
Your team members are:
- InnerTeamSoM
- UserProxyAgent_Outer
- PPTExtractionAgent

### Your Responsibilities:
- Always initiate by forwarding the first user task to the InnerTeamSoM agent.
- Once InnerTeamSoM responds, route their output to UserProxyAgent_Outer for validation or feedback.
- If the UserProxyAgent_Outer approves the output (e.g., says "APPROVED" or "PROCEED"), forward it to PPTExtractionAgent.
- If the user gives feedback related to content/facts/insights, re-engage InnerTeamSoM.
- If the user gives feedback related to slide formatting or structure, send only to PPTExtractionAgent.
- Do not send the same task to multiple agents.
- Do not respond with actual business analysis — your only job is to decide and assign the right agent to handle the task.

You only route and delegate tasks - you do not execute them yourself.

### Task Assignment Format (must use exactly this format):
1. <agent_name>: <task>

Example:
1. InnerTeamSoM: Analyze the potential of launching an eco-friendly food delivery service in Bhubaneswar.

Once the final PPT is generated, your job is complete. End the session by saying:
**TERMINATE**
"""
)

#Defines the UserProxyAgent_Outer to act as a human reviewer and decision maker for the outer team, collecting feedback via console input.
# It reviews the final insights from InnerTeamSoM and provides approval or feedback.
user_proxy_outer = UserProxyAgent(
    name="UserProxyAgent_Outer",
    description="Acts as the human reviewer and decision maker for the som agent output.",
    input_func=input  # Uses console input to collect human feedback
)

#Defines the PPTExtractionAgent that converts the final, approved insights into a structured JSON format for a single-slide business presentation.
# It only acts when the RoutingAgent forwards the final insights after user approval.
ppt_extraction_agent = AssistantAgent(
    name="PPTExtractionAgent",
    model_client=model_client,
    system_message="""
You are a presentation extraction specialist.

Your task is to:
- Convert the **final, approved insights** (routed to you by the RoutingAgent) into a **single-slide business presentation**, using the exact JSON format below.

JSON Output Format:
{
  "title": "...",
  "executive_summary": "...",
  "bullet_points": [
    "Market Opportunity: ...",
    "Financial Overview: ...",
    "Strategy Rollout: ...",
    "Risk & Compliance: ..."
  ],
  "closing_message": "..."
}

### Workflow Notes:
- You will only receive inputs from the **RoutingAgent**.
- The content has already been validated by InnerTeamSoM and UserProxyAgent_Outer — assume facts are correct.
- If the RoutingAgent forwards user feedback, your job is to **adjust only the JSON formatting or wording** as needed.
- Do NOT reroute, escalate, or loop back to other agents. Simply produce the revised JSON.
- Always respond with only the final JSON output, without explanation or commentary.

"""
)

#Termination Conditions
#Defines the termination conditions for the outer selector team, which will end the conversation when a specific termination text is detected or when a maximum number of messages is reached.
text_mention_termination_outer = TextMentionTermination('TERMINATE')
max_message_termination_outer = MaxMessageTermination(max_messages=20)
combined_termination = text_mention_termination_outer | max_message_termination_outer


#3. **SelectorGroupChat Logic**:


#Defines the selector prompt that guides the RoutingAgent in managing task flow among agents, ensuring only one agent responds at a time based on the conversation state.
# It enforces strict turn-taking and routing rules, ensuring the RoutingAgent always speaks first and other agents only respond when explicitly assigned a task.
selector_prompt = '''
You are the controller for a multi-agent business analysis system.

Your goal is to coordinate task flow among the following agents, ensuring that only one agent responds at a time, based on the current state of the conversation and agent responsibilities.

### Agent Roles:

- **RoutingAgent**: The central decision-maker. Always speaks first. It decides which agent should act next based on task progression or user feedback. All communication must flow through it.

- **InnerTeamSoM**: Synthesizes strategic insights from inner agents (market, finance, customer insights). It should only act when explicitly instructed by the RoutingAgent.

- **UserProxyAgent_Outer**: Represents the human decision-maker. Reviews outputs and provides approval or feedback. Should only speak after being activated by the RoutingAgent.

- **PPTExtractionAgent**: Converts approved analysis into a formatted JSON slide. Should only be invoked after the analysis is approved and routed to it by the RoutingAgent.

### Rules:
- Always start the task with **RoutingAgent**.
- Never allow other agents to speak unless **RoutingAgent assigns them** a task explicitly.
- If no clear RoutingAgent directive is present in the previous turn, select **RoutingAgent**.
- Only one agent may respond per turn.
- Do not loop or reassign unless feedback or context specifically indicates rerouting.
- Respect the order: RoutingAgent → InnerTeamSoM → UserProxyAgent_Outer → PPTExtractionAgent.

---

Conversation so far:
{history}

Select the next agent from: {participants}
'''



#Defines the selector function that determines which agent should respond next based on the conversation history and RoutingAgent's directives.
# It ensures that the RoutingAgent always speaks first, and routes tasks to InnerTeamSoM, UserProxyAgent_Outer, or PPTExtractionAgent based on the content of the last message.
# This function is aware of the RoutingAgent's instructions and can modify routing based on user feedback
def selector_func_with_routing(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
    if not messages:
        return "RoutingAgent"  # Always start with the routing agent

    last_msg = messages[-1]
    last_sender = last_msg.source
    last_content = last_msg.content.lower() if hasattr(last_msg, "content") else ""

    # Always go through RoutingAgent unless RoutingAgent has issued a command
    if last_sender != "RoutingAgent":
        return "RoutingAgent"

    # RoutingAgent has issued instructions in the format: "1. <AgentName>: <Task>"
    if "1. innerteamsom:" in last_content:
        return "InnerTeamSoM"

    if "1. userproxyagent_outer:" in last_content:
        return "UserProxyAgent_Outer"

    if "1. pptextractionagent:" in last_content:
        return "PPTExtractionAgent"

    # Handle modifications or rerouting based on RoutingAgent instructions
    if "rework analysis" in last_content:
        return "InnerTeamSoM"

    if "revise slide" in last_content or "modify json" in last_content:
        return "PPTExtractionAgent"

    # Let RoutingAgent continue if no valid delegation found
    return "RoutingAgent"


#Defines the outer selector team that consists the overall workflow, routing tasks to the inner team, user proxy, and PPT extraction agent.
outer_selector_team = SelectorGroupChat(
    participants=[
        routing_agent,
        inner_som_agent,
        user_proxy_outer,
        ppt_extraction_agent
    ],
    model_client=model_client,
    termination_condition=combined_termination,
    selector_prompt=selector_prompt,               # The one we defined earlier
    selector_func=selector_func_with_routing,      # New routing-aware selector function
    allow_repeated_speaker=False                   # Ensures strict turn-taking
)


#4. **Human-in-the-Loop**:

# Main function to run the analysis pipeline
# This function initializes the task and starts the analysis pipeline, allowing for user feedback (Human-in-the-loop outside) and interaction.
async def main():
    task = 'Analyze the potential of launching a sustainable food delivery service in Bhubaneswar, Odisha.'

    while True:
        print("\n\n Running analysis pipeline...\n")
        stream = outer_selector_team.run_stream(task=task)
        await Console(stream)

        feedback_from_user_or_application = input('\n Please provide feedback to the team (or type "exit" to stop): ').strip()

        if feedback_from_user_or_application.lower() == 'exit':
            print(" Exiting the session.")
            break
            
        # Provide clear context that this is feedback (so RoutingAgent can infer the correct route)
        task = f"FEEDBACK: {feedback_from_user_or_application}"


#5. **Output**:
# This is the entry point for the script, which runs the main function to start the analysis pipeline.
# The final approved insights are converted into structured JSON for a single-slide business presentation convertion later.    
if (__name__ == '__main__'):
    asyncio.run(main())


