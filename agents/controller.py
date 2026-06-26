import json
from agents.agent import Agent
from google.genai import types

class Controller(Agent):
    options = None    
    project = None
    engineer = None
    plan = None
    current_plan_step = None
    logger = None

    system_message = "You are the ReviewGPT Controller, a helpful scientific reviewing assistant. You manage several other AIs, passing directions to them from the user. You communicate directly with the other AIs, and as such your answers MUST be ONLY valid json."
    
    # 1. We define the JSON schema 
    controller_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "explanation": types.Schema(type=types.Type.STRING),
            "actor": types.Schema(type=types.Type.STRING),
            "action": types.Schema(type=types.Type.STRING),
            "parameters": types.Schema(type=types.Type.OBJECT)
        },
        required=["explanation", "actor", "action", "parameters"]
    )

    def __init__(self, logger) -> None:
        super().__init__()
        self.options = []
        self.current_plan_step = 0
        self.logger = logger

    def get_actions(self):
        return ["Actor: Controller | Action: Skip this step | Parameters: | Description: Skip the current step if it is unnecessary or impossible"]
    
    def set_plan(self, plan):
        self.plan = plan
    
    def interpret(self, action):
        if action.get("action") == "Start next plan step":
            return self.execute_next_step()
        elif action.get("action") == "Skip this step":
            return {"actor": "Controller", "action": "Skip this step", "description": "I skipped this step."}

    def set_options(self, options):
        self.options = options
    
    def choose_next_action(self):
        prompt = "You are currently following an overall plan to point out the weaknesses in the paragraph \""+self.plan.get_primary_paragraph()+"\"."

        if self.plan.get_next_step_counter() > 1:
            prompt += " This is a log of your progress so far:\n\n"
            prompt += self.plan.describe_resolutions_first_person()

        prompt += "\n\nThe remaining steps are:\n\n"
        prompt += self.plan.describe_remaining_steps()
        prompt += "\n\nThe next step is " + self.plan.describe_next_step()
        prompt += "\n\nYou will be given a list of actions. Your task is to decide what the best action to take is to accomplish the next step. Each action has several fields, separated by a vertical line (|). These are the actor who takes the action, the name of the action, the parameters that action requires, and a short description of the action. The options are:\n"
        prompt += "\n".join([" * " + o for o in self.options]) + "\n\n"
        prompt += "Provide the best action to take using the JSON schema."
        
        messages=[
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]

        # 2.Use the schema to build the JSON
        raw_result = self.send_message(messages, response_schema=self.controller_schema)
        
        try:
            action = json.loads(raw_result)
        except Exception as e:
            self.logger.log("System", f"JSON Parse Error: {e}")
            action = {"explanation": "Fallback due to JSON error", "actor": "Controller", "action": "Skip this step", "parameters": {}}

        self.logger.log("Controller", "I am executing step " + self.plan.describe_next_step() + " " + action.get("explanation", "").strip())
        act_str = action.get("action", "")
        if "parameters" in action and isinstance(action["parameters"], dict) and len(action["parameters"]) > 0:
            act_str += " (" + ", ".join([k+"="+str(v) for k,v in action["parameters"].items()]) + ")"

        self.logger.log("Controller", "I am asking the " + action.get("actor", "Nobody") + " to \"" + act_str + "\"")

        return action

    def parse(self, message):
        prompt = ""
        if len(self.plan.get_steps()) > 0:
            prompt += "Please note: You are currently following an overall plan. The step you are currently working on is " + str(1+self.current_plan_step) + " (" + self.plan.get_steps()[self.current_plan_step].describe()+"). The full plan is:\n"
            prompt += "\n".join([str(1+i) + ") " + x.describe() for i,x in enumerate(self.plan.get_steps())])
        else:
            prompt = "Warning: You are not currently following any plan. I suggest making one."

        prompt += "\n\nYou will be given a list of actions, and a message. Your task is to decide, given the message, what the best action to take is... The options are:\n"
        prompt += "\n".join([" * " + o for o in self.options]) + "\n\n"
        prompt += "The message is:\n" + message + "\n\n"
        
        messages=[
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]

        # Use the schema for instant JSON
        raw_result = self.send_message(messages, response_schema=self.controller_schema)
        
        try:
            result = json.loads(raw_result)
        except Exception:
            result = {"explanation": "Fallback due to JSON error", "actor": "Controller", "action": "Skip this step", "parameters": {}}

        result["message"] = message
        return result