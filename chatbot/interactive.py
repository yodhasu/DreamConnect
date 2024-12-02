import os
import re
from chatbot import useOllama
from chatbot import useGroq
from chatbot import useOpenAI
from chatbot import sendToBackend
from chatbot import context_logger
from datetime import datetime
from urlextract import URLExtract
import base64
import json

extractor = URLExtract()
class interactiveChat:
    def __init__(self, affection = 10, user=None, bio=None, context = None, char = "AI Girlfriend", chat_engines = "groq", system_prompt = None, user_prompt = None, sys_prompt_dir = None, usr_prompt_dir = None, charnickname = None):
        if user is None or bio is None:
            raise ValueError("'user' and 'bio' must be provided.")
        
        self.engine = chat_engines.lower()
        if self.engine.lower() not in ["ollama", "g4f", "openai", "groq"]:
            raise ValueError(" Current available chat engines are: 'Ollama', 'openai', 'g4f', 'Groq'")
        
        self.charater = char
        self.affection = affection
        self.user = user
        self.bio = bio
        self.context = context or ""
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.system_prompt_from_directory = sys_prompt_dir or "chatbot/system_prompt.txt"
        self.user_prompt_from_directory = usr_prompt_dir or "chatbot/user_prompt.txt"
        self.back = sendToBackend.backend()
        self.logger = context_logger.ContextLogger()
        self.getPromptFromDir()
        self.response = ""
        self.char_nick = charnickname
        self.feedback = ""
        self.back.send_to_space(["neutral"])
        
    # Funtion to setup prompt
    def getPromptFromDir(self):
        # get system prompt
        try:
            # print(self.system_prompt_from_directory)
            if self.system_prompt is None:
                with open(self.system_prompt_from_directory, "r") as sysprompt:
                    self.system_prompt = sysprompt.read()
        except Exception as e:
            raise(f"Error opening system prompt with error: {e}")
        # get user prompt
        try:
            # print(self.user_prompt_from_directory)
            if self.user_prompt is None:
                with open(self.user_prompt_from_directory, "r") as usrprompt:
                    self.user_prompt = usrprompt.read()
        except Exception as e:
            raise(f"Error opening user prompt with error: {e}")
    
    
    # Define chat engine based on user
    def defineEngine(self, engine = None, api_key = None, chat_model = None, parameter = None):
        if self.engine is None:
            if engine is None:
                raise ValueError("engine can't be empty")
            self.engine = engine
        else:
            pass
        
        if self.engine.lower() not in ["ollama", "g4f", "openai", "groq"]:
            raise ValueError(" Current available chat engines are: 'Ollama', 'openai', 'g4f', 'Groq'")
        
        # make different case depends on engine
        self.chatClient = None
        match self.engine:
            case "ollama":
                self.chatClient = useOllama.ChatEngine()
            case "groq":
                self.chatClient = useGroq.ChatEngine(api_key=api_key)
            case "openai":
                self.chatClient = useOpenAI.ChatEngine(api_key=api_key)
            case _:
                raise ValueError("Wrong engine/engine provided")
    
    def classifyFeedback(self, text):
        if text in ["y", "yes"]:
            self.feedback = "good"
        elif text in ["n", "no"]:
            self.feedback= "bad"
        else:
            self.feedback = "neutral"
    
    def imageVision(self, imgpath):
        print(f"Image path: {imgpath}")
        result = self.chatClient.groqVision(img_path=imgpath)
        return result
    
    # chat function
    def makeChat(self, usr_input = None, api_key = None):
        # define engine
        self.defineEngine(api_key=api_key)
        # auto update memory logs
        if len(self.logger.get_context_log()) == 15:
            self.save_logs()
        # get prompt
        self.getPromptFromDir()
        # get memory
        curr_memory = "\n"+ self.retrieve_memory(api_key=api_key) or ""+ "\n"
        # identify user's intention
        intention = self.intentIdentifier(usr_input, self.response, api_key)
        # check for images in user input
        img_summarized = ""
        status, img = self.filterFilepath(usr_input)
        # print(status, img)
        # Formating input to prompt
        
        local_system_prompt = self.system_prompt
        local_user_prompt = self.user_prompt
        
        local_system_prompt = local_system_prompt.format(
            user = self.user,
            userbio = self.bio,
            char = self.charater
        )
        
        local_user_prompt=local_user_prompt.format(
            intention = intention,
            date = str(datetime.now()),
            time = self.get_time_of_day(),
            memory = curr_memory or "None",
            context = self.logger.get_context_log() or self.context,
            affection = self.affection,
            question = usr_input
        )
        # add image summary to the prompt
        if status != 0:
            img_summarized = self.imageVision(img)
            local_user_prompt += f"\n\nSummary of given image by user: {img_summarized}\n\nBy having summary of the image given by user that means you can SEE the image and please tell what you see."
        
        
        
        print(f"Context: {local_user_prompt}\n")
        response = self.chatClient.process_query(query=local_user_prompt, system_prompt=local_system_prompt, inputs=usr_input)
        self.back.send_to_space(response)
        # Debugging print to check the response
        # print(f"Generated response: {response}")
        
        if response is None:
            print("No response generated.")
            return

        print(f"\n{self.charater}: {response}\n")
        self.response = response
        self.logger.log_context(usr_input, response, self.feedback)
        self.context = self.logger.get_context_log()
        return response
    
    def save_logs(self):
        filename = f"chatbot/logs/logfile_{str(datetime.now())}".replace(":", "-")
        filename = filename.replace(".", "-")
        self.logger.save_context_log(filename=f"{filename}.json")

    def retrieve_memory(self, api_key=None, log_dir="chatbot/logs/", max_logs=1):
        memory = ""
        
        chatengine = useOllama.ChatEngine()

        # Get a list of all log files sorted by name (only JSON files now)
        log_files = sorted(
            [os.path.join(log_dir, log) for log in os.listdir(log_dir) if log.endswith(".json")],
            reverse=True  # Sort by name in descending order (latest logs first)
        )
        
        # Limit to the most recent `max_logs` files
        recent_logs = log_files[:max_logs]
        
        # Process the most recent logs
        for log_path in recent_logs:
            print("Processing log file at path:", log_path)
            with open(log_path, "r") as logfile:
                # Read the log entries (now they are in JSON format)
                logs = json.load(logfile)  # This loads the logs as a list of dictionaries
                
                # Iterate through each log entry and format it
                for log in logs:
                    # Create a clean format for each log entry
                    log_text = f"""
                    Timestamp: {log['Timestamp']}
                    User message: {log['User message']}
                    User emotion: {log['User emotion']}
                    AI Response: {log['AI Response']}
                    AI emotion: {log['AI emotion']}
                    Off-topic response: {log['Off topic response']}
                    Response quality: {log['Overall Response quality']}
                    Repetitive response: {log['Repetitive response']}
                    """
                    memory += log_text + "\n"
            
        # Construct the summarize prompt
        summarize_prompt = f"""
        You are {self.charater} also called as {self.char_nick}.
        
        You and I, {self.user}, also known as User are having a chat previously and you need to summarize it so you know:
        - What happened.
        - Important details.
        - How you feel.
        """
        
        # Use the summarizer model to generate the summary of the memory
        retrieved_memory = chatengine.generate_response(memory, summarize_prompt)
        
        return retrieved_memory if memory != "" else ""

    
    def intentIdentifier(self, user_input, char_response, api_key):
        
        prompt = f"""
        This is the character's previous input : {char_response}
        Character's name: {self.charater}
        Character's nickname: {self.char_nick}
        you may use or not use it to do your task.
        IF NO PREVIOUS SYSTEM RESPONSE PROVIDED JUST FOCUS ON USER'S INPUT!
        
        
        Your task is:
        Identify the intention of the user's input.
        
        User's input {user_input}
        DO NOT USE ANY TOOLS! YOU ARE NOT ALLOWED TO USE ANY TOOLS!
        """
        system_prompt = "You are a smart AI that is used to identify intention of the user's input in a chat between character and user. Answer in paragraph but limit your answer to 20 - 70 token"

        intent = self.chatClient.generate_response_for_utils(context=user_input, rules=system_prompt)
        return intent
    
    
    def filterFilepath(self, textinput):
        path_pattern = r'["\']?([a-zA-Z]:[\\\/][^<>:"|?*]+(?:[\\\/][^<>:"|?*]+)*)["\']?'
        match = re.findall(path_pattern, textinput)
        urlfound = extractor.find_urls(textinput)
        
        if len(urlfound) >=1:
            return 2, urlfound[0]
        else:
            if match:
                file_path = match[0]
                
                # Replace backslashes with forward slashes in the file path
                processed_path = file_path.replace("\\", "/")
                
                # encode to base64
                encoded_image = self.encode_image(processed_path)
                local_image = f"data:image/jpeg;base64,{encoded_image}"
                
                return 1, local_image
            else:
                return 0, ""
    
    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    @staticmethod
    def get_time_of_day():
        """Return the current time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "night"
                