#load in environment variables
from dotenv import load_dotenv


load_dotenv()

#set prompt as a string
from llama_index.core.tools import ToolMetadata
from llama_index.core.selectors import LLMSingleSelector


reflection = """
This choice involves making an explicit statement about wanting to reflect on specific past events in your life where you experienced strong emotions or challenges. It prompts you to recall and describe moments when you felt lost, alone, inadequate, or not good enough. Examples include:

            'Give me a time where I felt lost and alone in my life.'
            'Tell me a time where I felt like I was not enough.'
            'Describe a time where I felt like I was not good enough.'
            'Give me a time when I went out to the park and tried to do XYZ.'
            'Give me a time when I went on an adventure with some friends.'
            'Give me a time when I was sad and lonely.'
            Based on this understanding, classify the following input as reflecting on a past event or experience." 
"""

guided = """
This choice focuses on articulating the current thoughts and feelings that are on your mind. It involves expressing the emotions or mental states you are experiencing in the present moment, such as anxiety, difficulty concentrating, restlessness, or inability to focus. Examples include:

            'I had a good day, and I'm doing XYZ today, and I also went to play basketball.'
            'I went to the park with some friends, and we did XYZ.'
            'I'm feeling a little sad today, and it's because I failed an exam.'
            'Feeling anxious.'
            'Not able to focus.'
            'Feeling restless.'
            'Not able to concentrate.'
            Based on this understanding, classify the following input as articulating current thoughts or feelings.
"""
# choices as a list of strings
choices = [
    reflection,
    guided,
]

#promtp for the selector

selector = LLMSingleSelector.from_defaults()
selector_result = selector.select(
    choices, query="Give me a time where i was exited for a trip"
)
print(selector_result.selections)