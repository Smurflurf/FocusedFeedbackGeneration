import os
#os.environ["HF_HUB_OFFLINE"] = "1"
#os.environ["TRANSFORMERS_OFFLINE"] = "1"
#os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# -> comment this in if you ran everything once, to use the offline models

from room.room import Room
from utils.logger import Logger
import config

logger = Logger()
room = Room(logger)
logger.log("Controller", room.greet())
print("Enter the paragraph you would like to have reviewed:")
paragraph = input(" > ")
print("Enter the link of the paper:")
paper_link = input(" > ")

result = room.main_loop(paragraph, paper_link, config.instruction)