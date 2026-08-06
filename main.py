from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from app.agents.multiagent import multi_agent_system
import uvicorn
import os

app = FastAPI(
    title="Multi-Task Agent Platform",
    docs_url="/docs"
)

# Serve the index.html Web UI at the root "/"
@app.get("/", response_class=FileResponse)
def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html file not found"}

# Request Model
class AgentQueryRequest(BaseModel):
    message: str = Field(..., example="Write a Python script to reverse a string")
    thread_id: str = Field(default="web_session")

# Response Model
class AgentQueryResponse(BaseModel):
    status: str
    user_query: str
    agent_response: str
    thread_id: str

# Agent Chat API Endpoint
@app.post("/api/v1/chat", response_model=AgentQueryResponse)
def chat_with_agents(request: AgentQueryRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        # Invoke agent system
        result = multi_agent_system.invoke(inputs, config=config)
        last_message = result["messages"][-1].content if result.get("messages") else "No response."
        
        return AgentQueryResponse(
            status="success",
            user_query=request.message,
            agent_response=last_message,
            thread_id=request.thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)