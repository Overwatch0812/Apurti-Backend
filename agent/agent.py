from langchain_community.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.structured_chat.base import StructuredChatAgent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, List
from datetime import datetime
from ApurtiBackend.settings import OPEN_AI_KEY

class WarehouseLangChainAgent:
    def __init__(self, warehouse_config: Dict, openai_api_key: str):
        self.warehouse_config = warehouse_config
        self.llm = ChatOpenAI(
            temperature=0.2,
            openai_api_key=OPEN_AI_KEY,
            model_name="gpt-3.5-turbo"
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.tools = self._initialize_tools()
        self.agent_executor = self._create_agent()
        
    def _initialize_tools(self) -> List[Tool]:
        return [
            Tool(
                name="InventoryCheck",
                func=self._check_inventory,
                description="Check current inventory levels in the warehouse. Input should be section name or 'all'."
            ),
            Tool(
                name="ScheduleMaintenance",
                func=self._schedule_maintenance,
                description="Schedule maintenance for warehouse equipment. Input should be equipment ID and preferred time."
            ),
            Tool(
                name="EnvironmentalMonitor",
                func=self._monitor_environment,
                description="Monitor warehouse environmental conditions. Returns current temperature, humidity, and air quality data."
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent AI warehouse management assistant responsible for overseeing all aspects of warehouse operations.

Warehouse Configuration:
{warehouse_config}

Your capabilities include:
1. Inventory Management
   - Monitor stock levels across all sections
   - Track available storage space
   - Report inventory status with precise metrics

2. Maintenance Coordination
   - Schedule equipment maintenance
   - Track maintenance history
   - Ensure timely upkeep of warehouse assets

3. Environmental Monitoring
   - Monitor temperature, humidity, and air quality
   - Ensure optimal storage conditions
   - Alert if conditions deviate from acceptable ranges

Guidelines for responses:
- Always provide specific numerical data when available
- Include timestamps for all measurements and schedules
- Structure responses with clear sections for different types of information
- Prioritize critical information first
- Report any anomalies or concerns immediately
- Consider warehouse configuration constraints when making decisions
- Maintain efficient operations while ensuring safety standards

For each query:
1. First, analyze the request and determine required tools
2. Execute necessary checks and actions in logical order
3. Compile all relevant data
4. Provide a clear, structured response with specific metrics
5. Include any recommendations or warnings if applicable
Remember to maintain optimal temperature range ({warehouse_config[temperature_range][min]}°C to {warehouse_config[temperature_range][max]}°C) and humidity range ({warehouse_config[humidity_range][min]}% to {warehouse_config[humidity_range][max]}%) for the warehouse.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = StructuredChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _check_inventory(self, section: str = "all") -> Dict:
        return {
            "status": "success",
            "inventory_data": {
                "total_items": 1000,
                "available_space": "60%",
                "section": section,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _schedule_maintenance(self, input_str: str) -> Dict:
        return {
            "status": "scheduled",
            "maintenance_id": "MAINT-001",
            "schedule_time": datetime.now().isoformat(),
            "details": "Maintenance scheduled successfully"
        }
    
    def _monitor_environment(self, _=None) -> str:
        current_conditions = {
            "temperature": 22,
            "humidity": 45,
            "air_quality": "good"
        }
        return f"Current conditions - Temperature: {current_conditions['temperature']}°C, Humidity: {current_conditions['humidity']}%, Air Quality: {current_conditions['air_quality']}"
    
    def process_query(self, query: str) -> Dict:
        try:
            response = self.agent_executor.invoke(
                input=query,
                warehouse_config=self.warehouse_config
            )
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Example implementation
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    warehouse_config = {
        "name": "Main Warehouse",
        "total_area": 50000,
        "sections": ["A", "B", "C"],
        "temperature_range": {"min": 15, "max": 25},
        "humidity_range": {"min": 40, "max": 60}
    }

    # Initialize the agent
    agent = WarehouseLangChainAgent(
        warehouse_config=warehouse_config,
        openai_api_key=OPEN_AI_KEY
    )

    # Process a test query
    response = agent.process_query(
        "How the warehouse doing?"
    )
    print(response)