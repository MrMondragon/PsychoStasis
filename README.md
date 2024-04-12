**PsychoStasis**

This is a study project with the following goals:

- Support for many agents communicating between each other and with the user in a forum like 
environment, fully controllable through authoritative commands by the user directly on the chat UI 
- Each agent can work based on a different model (either local or remote), with a system that optimizes 
resources use through dynamically loading and unloading necessary models on the background 
- Also, even for agents operating over the same model, there’s the possibility to dynamically load 
LoRAs in order to make the agent more of an expert on a given field or set of skills 
- Several layers of memory based on a vectorial search mechanism that mimic human memory 
organization 
- Both individual and group memory, allowing for agent growth, learning, specialization and 
individuation over time. 
- Dynamic context window, enriched through RAG systems and capable of switching between context 
and sub-context in order to perform specific tasks 
- Support of several model architectures and chat formats, going from task-specific BERT models, used 
as ‘sub-models’ in cognitive processes, to current state of the art models like Mistral, Llama and 
ChatGPT (accessed through APIs) 
- Dynamic background cognitive system, based on human cognitive processes, to implement 
functionalities such as: 
  o Deciding which information to commit to memory, when and to which layer 
  o Consolidating memory between the functional, episodic memory and a more Summarized 
layer 
  o Memory enrichment, adding metadata such as entities, impressions about user sentiment and 
feedback and web-search keywords to memory entries 
  o Deciding when such enrichment is needed and when it is irrelevant 
  o Reading large documents on a number of formats and processing them in a specialized 
    documental memory for further reference 
  o Enriching the context with memory data, as well as web search results 
  o Starting training sessions on specific corpora or memory segments conversationally in order 
    to generate LoRA models to be loaded by the agents as mentioned before 
  o Summarization and NER analysis of text 
  o Fact extraction and conversation classification 
- Use of tools such as web-search and external API’s 
- Ability to generate and execute code
- Use of grammar files to enable consistent output for function calling and other tasks 
- Developed in python, using PyTorch, Llama.cpp for python, Transformers and many other libraries.

Observations:
- I am deliberately not using some tools and libs (like Langchain and Agent frameworks) because one of the goals of this project is to implement things similar to what those libraries do in order to study and learn.
- Part of the code on the model loaders was heavily inspired by the code of oobabooga's own model loaders

