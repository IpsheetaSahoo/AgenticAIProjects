**🧠  Agentic Business Strategy Planner with Society-of-Mind and Human-in-the-Loop Coordination**

🛍️ Overview

This project implements a modular, multi-agent business analysis system using Microsoft AutoGen (stable version). It is designed to:

Analyze complex business proposals

Coordinate between expert agents

Incorporate human-in-the-loop (HITL) feedback

Produce an executive-ready summary slide in JSON format

**
🏗️ Architecture Diagram
**




                            +-------------------+
                            |   Human Operator  |
                            +-------------------+
                                     |
                                     v
                            +-------------------+
                            |   RoutingAgent    |
                            +-------------------+
                                     |
                 +-------------------+------------------+
                 |                   |                  |
                 v                   v                  v
        +--------------------+  +---------------------+  +------------------------+
        |   InnerTeamSoM     |  | UserProxyAgent_Outer|  |  PPTExtractionAgent    |
        | (Society of Mind)  |  +---------------------+  +------------------------+
        |                    |             |                      |
        | + MarketAnalyst    |             |                      |
        | + FinancialModeler |             |                      v
        | + CustomerInsight  |             |          +--------------------------+
        | + UserProxy_Inner  |             +--------> |  JSON Slide Output       |
        +--------------------+                        +--------------------------+

**🧠 Agent Roles**

🔹 InnerTeamSoM (Society of Mind)

A SocietyOfMindAgent that wraps a RoundRobinGroupChat among the following participants:

MarketAnalystAgent

FinancialModelAgent

CustomerInsightAgent

UserProxyAgent_Inner (Human-in-the-loop feedback)

🔹 RoutingAgent

An AssistantAgent responsible for orchestrating the entire workflow:

Routes the initial task to InnerTeamSoM

Passes the output to UserProxyAgent_Outer

Sends approved output to PPTExtractionAgent

Accepts human feedback and redirects accordingly

Prevents unnecessary routing (e.g., avoids re-routing to InnerTeamSoM for PPT-related edits)

🔹 UserProxyAgent_Outer

Validates and provides feedback on outputs from the InnerTeamSoM and optionally the PPTExtractionAgent.

🔹 PPTExtractionAgent

Generates a single-slide business presentation in a strict JSON format, based on approved content.

**
🔁 Workflow Logic**

Start: RoutingAgent receives a user task.

Analysis: Routes task to InnerTeamSoM → inner experts collaborate and generate analysis.

Validation: InnerTeamSoM output sent to UserProxyAgent_Outer for approval.

Presentation: On approval, RoutingAgent sends data to PPTExtractionAgent.

Output: Final JSON slide is shown.

Feedback: Human can provide feedback → RoutingAgent routes appropriately to either InnerTeamSoM or PPTExtractionAgent depending on feedback scope.

**📥 Sample Output**

<img width="1445" height="287" alt="image" src="https://github.com/user-attachments/assets/e26d3a98-612e-4411-8cdb-b231ef34b79b" />




**🚀 How to Run**

python SoM_HITL_Business_Strategy_Agentic_Pipeline.py

To observe the full flow of agent and human interactions for debugging or demonstration, check the output.lua file located in the project folder. 
It logs step-by-step decisions made by the RoutingAgent, validation steps, and human feedback integration.







