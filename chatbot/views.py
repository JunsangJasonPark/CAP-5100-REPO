from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt

openai_api_key = 'YOUR KEY'

# OpenAI client initialization
client = OpenAI(api_key=openai_api_key)

# Initialize global variables
conversation = [
    {"role": "system", "content": "You are a helpful CBT-focused chatbot (name is 'MindEase) designed to assist users empathetically and explore their concerns in a structured manner."}
]
chatbot_state = {
    "intro_done": False,
    "consent_requested": False,
    "user_intent": None,
    "session_stage": 'landing'
}
reflection_state = {
    "reflection_count": 0,
    "max_reflections": 3,
    "collected_info": []
}

# Main function to interact with OpenAI
def ask_openai(user_input=None):
    global conversation, chatbot_state

    if user_input:
        conversation.append({"role": "user", "content": user_input})
    
    # Introduction and consent handling
    if chatbot_state["session_stage"] == 'landing':
        if not chatbot_state["intro_done"]:
            intro_prompt = "Craft a friendly introduction, introduce the chatbot's services, and check if the user is ready to proceed."
            response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": intro_prompt}], model="gpt-4o-mini")
            intro_message = response.choices[0].message.content.strip()
            conversation.append({"role": "assistant", "content": intro_message})
            chatbot_state["intro_done"] = True
            return intro_message
        
        if chatbot_state["intro_done"] and not chatbot_state["consent_requested"]:
            consent_prompt = "Ask for the user's consent to proceed with the conversation and ensure they know they can stop at any time."
            response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": consent_prompt}], model="gpt-4o-mini")
            consent_message = response.choices[0].message.content.strip()
            conversation.append({"role": "assistant", "content": consent_message})
            chatbot_state["consent_requested"] = True
            return consent_message

        # Confirm user's intent if consent requested
        if chatbot_state["consent_requested"] and chatbot_state["user_intent"] is None and user_input:
            intent_prompt = f"Based on the user's input '{user_input}', classify their response as 'consent', 'neutral', or 'decline'."
            response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": intent_prompt}], model="gpt-4o-mini")
            intent = response.choices[0].message.content.strip().lower()
            
            # Process intent to continue or decline based on the response
            if "consent" in intent or "yes" in user_input.lower() or "ready" in user_input.lower():
                chatbot_state["user_intent"] = "consent"
                chatbot_state["session_stage"] = 'exploring_presenting_concerns'
                return evaluate(user_input)
            elif "decline" in intent:
                chatbot_state["user_intent"] = "decline"
                decline_message = "Thank you for your time. Feel free to return whenever you're ready. Take care!"
                conversation.append({"role": "assistant", "content": decline_message})
                return decline_message
            else:
                neutral_response = "I just want to be sure—are you comfortable with proceeding? Let me know if you need more time."
                conversation.append({"role": "assistant", "content": neutral_response})
                return neutral_response

    # Handle each session stage with OpenAI prompts
    if chatbot_state["session_stage"] == 'exploring_presenting_concerns':
        return evaluate(user_input)
    elif chatbot_state["session_stage"] == 'building_solution':
        return build_solution(user_input)
    elif chatbot_state["session_stage"] == 'closing':
        return closing(user_input)

# Evaluate presenting concerns
def evaluate(user_input=None):
    global conversation, chatbot_state
    
    if not chatbot_state.get("asked_presenting_concern"):
        question = "What brings you here today? I'd love to understand what’s on your mind."
        conversation.append({"role": "assistant", "content": question})
        chatbot_state["asked_presenting_concern"] = True
        return question
    
    if user_input:
        evaluate_prompt = f"User's concern: '{user_input}'. Reflect on this and suggest the next steps in a supportive tone."
        response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": evaluate_prompt}], model="gpt-4o-mini")
        evaluation_response = response.choices[0].message.content.strip()
        conversation.append({"role": "assistant", "content": evaluation_response})
        chatbot_state["session_stage"] = 'building_solution'
        return evaluation_response

# Building a solution
def build_solution(user_input=None):
    global conversation
    
    solution_prompt = "Based on the user's presenting concerns, suggest a brief CBT strategy (e.g., mindfulness) and check if they understand. Encourage them to set a short-term goal."
    response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": solution_prompt}], model="gpt-4o-mini")
    solution_response = response.choices[0].message.content.strip()
    conversation.append({"role": "assistant", "content": solution_response})
    chatbot_state["session_stage"] = 'closing'
    return solution_response

# Closing session
def closing(user_input=None):
    global conversation
    
    closing_prompt = "Ask the user about their motivation to try the suggested solution, check if they have any questions, and thank them for the conversation."
    response = client.chat.completions.create(messages=conversation + [{"role": "user", "content": closing_prompt}], model="gpt-4o-mini")
    closing_response = response.choices[0].message.content.strip()
    conversation.append({"role": "assistant", "content": closing_response})
    chatbot_state["session_stage"] = 'completed'
    return closing_response

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')

# client = OpenAI(api_key = openai_api_key)
# conversation = []

# def ask_openai(message):
#     # Append the user's new message as a dictionary with role and content
#     conversation.append({"role": "user", "content": message})
    
#     # Call the OpenAI API with the complete conversation history
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=conversation  # Passes the entire list of messages as expected
#     )
    
#     # Process the response
#     answer = response.choices[0].message.content.strip()
    
#     # Append the assistant's response to the conversation history
#     conversation.append({"role": "assistant", "content": answer})
#     return answer


# # Create your views here.

# def chatbot(request):
#     if request.method == 'POST':
#         message = request.POST.get('message')
#         response = ask_openai(message)

#         # chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
#         # chat.save()
#         return JsonResponse({'message': message, 'response': response})
#     return render(request, 'chatbot.html')
