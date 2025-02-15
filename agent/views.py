from django.shortcuts import render
from django.http import HttpResponse
from .agent import *
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json

from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
import re
from ApurtiBackend.settings import OPEN_AI_KEY

def Home(request):
    return HttpResponse("heloooo")

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:5173"
    client_class = OAuth2Client

def parse_agent_response(agent_response):
    """Parse and structure the agent's response"""
    if agent_response.get('status') == 'error':
        return {'error': agent_response['message']}
    
    # Initialize the structured response
    structured_response = {
        'observation': {},
        'thought': "",
        'action': "",
        'final_answer': None
    }

    response_data = agent_response['response']
    
    if isinstance(response_data, str):
        # Extract data using regex patterns
        observation_match = re.search(r'Observation: ({.*?})', response_data)
        if observation_match:
            try:
                structured_response['observation'] = json.loads(observation_match.group(1))
            except json.JSONDecodeError:
                pass
        
        thought_match = re.search(r'Thought:(.*?)(?=\n|Action:|$)', response_data)
        if thought_match:
            structured_response['thought'] = thought_match.group(1).strip()
        
        action_match = re.search(r'Action:(.*?)(?=\n|Observation:|$)', response_data)
        if action_match:
            structured_response['action'] = action_match.group(1).strip()
        
        final_answer_match = re.search(r'"action": "Final Answer".*?"action_input": "(.*?)"', response_data)
        if final_answer_match:
            structured_response['final_answer'] = final_answer_match.group(1)
        else:
            # If we can't find the specific format, look for the last meaningful output
            structured_response['final_answer'] = response_data.strip()
    
    elif isinstance(response_data, dict):
        # If it's already a dictionary, try to extract known fields
        structured_response.update({
            'observation': response_data.get('observation', {}),
            'thought': response_data.get('thought', ""),
            'action': response_data.get('action', ""),
            'final_answer': response_data.get('output') or response_data.get('final_answer')
        })
    
    # Clean up empty values
    structured_response = {k: v for k, v in structured_response.items() if v}
    
    return structured_response

def Query(request):
    warehouse_config = {
        "name": "Main Warehouse",
        "total_area": 50000,
        "sections": ["A", "B", "C"],
        "temperature_range": {"min": 15, "max": 25},
        "humidity_range": {"min": 40, "max": 60}
    }
    agent = WarehouseLangChainAgent(
        warehouse_config=warehouse_config,
        openai_api_key=OPEN_AI_KEY
    )

    # Process a test query
    response = agent.process_query(
        "Please check the inventory levels in section A and schedule maintenance for forklift FL-101 for tomorrow morning. Also, what are the current environmental conditions?"
    )
    structured_res=parse_agent_response(response)
    if isinstance(response.get('response'), dict):
            intermediate_steps = response['response'].get('intermediate_steps', [])
            for step in intermediate_steps:
                action, observation = step
                if isinstance(observation, dict):
                    structured_res['observation'] = observation
                if isinstance(action, dict):
                    structured_res['action'] = action.get('tool')
                    structured_res['thought'] = action.get('log')
    return JsonResponse(structured_res)

# Create your views here.
@api_view(['POST'])
def warehouse_query_view(request):
    try:
        # Get the query from request data
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'Query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize the warehouse agent
        warehouse_config = {
            "name": "Main Warehouse",
            "total_area": 50000,
            "sections": ["A", "B", "C"],
            "temperature_range": {"min": 15, "max": 25},
            "humidity_range": {"min": 40, "max": 60}
        }
        agent = WarehouseLangChainAgent(warehouse_config=warehouse_config,openai_api_key=OPEN_AI_KEY)
        
        # Get the agent's response
        agent_response = agent.process_query(query)
        
        # Extract and structure the relevant information
        structured_response = parse_agent_response(agent_response)
        
        return Response(structured_response, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )