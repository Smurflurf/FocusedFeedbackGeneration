import json
from agents.agent import Agent
from google.genai import types

class Reviewer(Agent):
    options = None
    system_message = "You are the ReviewGPT Reviewer, a world class AI assistant for scientific reviewers. You write a review that highlights the weaknesses and areas of improvements of a paragraph based on context given to you, and return results as valid JSON."
    
    # JSON Schema for the review output
    reviewer_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "label": types.Schema(type=types.Type.STRING),
            "review": types.Schema(type=types.Type.STRING),
            "reasoning": types.Schema(type=types.Type.STRING)
        },
        required=["label", "review", "reasoning"]
    )

    def set_options(self, options):
        self.options = options
               
    def write_review(self, paragraph, plan, instruction):
        prompt = "You will be given a paragraph with the following context:\n\n"

        try:
            prompt += plan.get_question_answer_evidence()
        except:
            print("No context found")

        prompt += """There are five possible review labels: Empirical and Theoretical Soundness, Meaningful Comparison, Substance, Originality, Replicability. Write a review that:
                     1- Selects and quotes a substring from the given paragraph.
                     2- Chooses the appropriate review label 
                     3- Writes a review sentence that points out a weakness or suggests an improvement (if needed) using the quoted substring, the review label and the context. It is IMPORTANT that you use the provided context to generate a sensible review.  
                     4- Generates JSON object with the keys \"reasoning\",\"review\" and \"label\". Below are examples that follow all these rules, use them as inspiration: \n """ + instruction

        prompt += "Paragraph: " + paragraph

        messages=[
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]

        # Use JSON schema
        result_message = self.send_message(messages, response_schema=self.reviewer_schema)
        
        try:
            parsed_result = json.loads(result_message)
            print("\n================ FINISHED REVIEW ================\n")
            print(json.dumps(parsed_result, indent=4))
        except Exception as e:
            print("Could not parse reviewer JSON.", result_message)
        
        return 1
   
    def get_actions(self):
        return [
            "Actor: Reviewer | Action: Write review | Parameters: | Description: Write a review that only points out the weaknesses and areas of improvement of a passage based on the plan so far. Can only be called once context has been gathered by another agent."
        ]
    
    def interpret(self, action):
        if action["action"] == "Write review":
            return self.write_review(action["paragraph"], action["plan"], action["instruction"])
        else:
            return {
                "actor": "Reviewer",
                "description": "This action is not in my set of possible instructions.",
                "action": action["action"]
            }