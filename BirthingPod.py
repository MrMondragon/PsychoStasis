import gradio as gr
from Proxy import Proxy
from Nexus import globalNexus, Nexus
from PIL import Image, ImageOps
from Logger import globalLogger
import os

lora_path = 'lora\\' 


class BirthingPod(object):
  def __init__(self):
    self.activeProxy = None

  def createProxy(self, name, modelName, lora):
    self.activeProxy = Proxy(name=name) 
    if(modelName):
      modelName = modelName.split(".")[0]
      self.activeProxy.modelName = modelName
    if(lora):
      cwd = os.getcwd()
      workPath = os.path.join(cwd, lora_path)
      workPath = os.path.join(workPath, lora)
      self.activeProxy.LoRa = workPath
    globalLogger.log(f"Created proxy {self.activeProxy.name} with model {self.activeProxy.modelName} and lora {self.activeProxy.LoRa}")
       
  def setPrimer(self, primer):
    self.activeProxy.primer = primer
  
  def interrogatePrimer(self, prompt):
    result = self.activeProxy.GenerateAnswer(prompt=prompt)
    return result

  def UI(self):
    with gr.Blocks() as pod:
      gr.Markdown("# PsychoStasis - BirthingPod")
      with gr.Row():
        with gr.Column(scale = 3):
          txtName = gr.Textbox(label="Name")
        with gr.Column(scale = 3):
          modelSelector =gr.Dropdown(label="Model", choices=Nexus.GetModelList())
      with gr.Row():
        loraSelector = gr.Dropdown(label="Lora", choices=Nexus.GetLoraList())  
      with gr.Row():
        btnCreate = gr.Button("Create Proxy", )
        btnCreate.click(self.createProxy, inputs=[txtName, modelSelector, loraSelector])
      with gr.Row():
        txtPrimerPrompt = gr.Textbox(label="Primer", value="Give me a prompt that would define you, your world view. Start with 'I am a...'")
      with gr.Row():
        txtPrimer = gr.Textbox(label="Primer", lines=2)
      with gr.Row():
        btnInterrogatePrimer = gr.Button("Interrogate Primer")
        btnInterrogatePrimer.click(self.interrogatePrimer, inputs=[txtPrimerPrompt], outputs=[txtPrimer])
        btnSetPrimer = gr.Button("Set Primer")
        btnSetPrimer.click(self.setPrimer, inputs=[txtPrimer])
      with gr.Row():
        txtTenetPrompt = gr.Textbox(label="Tenet", value="List at the least four of what you consider your core values, your tenets.")
      with gr.Row():
        btnInterrogateTenet = gr.Button("Interrogate Tenet")
      with gr.Row():
        txtTenet = gr.Textbox(label="Tenet", lines=5)    
      with gr.Row():
        btnSetTenet = gr.Button("Set Tenet")
        btnResetTenet = gr.Button("Reset Tenet")
      with gr.Row():
        txtTagsPrompt = gr.Textbox(label="Tags", value="Now give me a few (at the least seven) tags that I could use to classfy you. These tags should contain no more than 2 words each.")
      with gr.Row():
        btnInterrogateTags = gr.Button("Interrogate Tags")
      with gr.Row():
        txtTags = gr.Textbox(label="Tags", lines=1)
      with gr.Row():
        btnSetTags = gr.Button("Set Tags")
        btnResetTags = gr.Button("Reset Tags")    
      with gr.Row():
        gr.Markdown("Parameters")
      with gr.Row():
        sldTemperature = gr.Slider(label="Temperature", value=0.7, maximum=1)
        txtPerson = gr.Textbox(label="Person", lines=1, value="1st")
        txtInnerPersona = gr.Textbox(label="Inner Persona", lines=3, value="These are my private thoughts. Here I will feel free to express my most intimate feelings and desires")
      with gr.Row():
        btnSetParams = gr.Button("Set Parameters")
        btnResetParameters = gr.Button("Reset Parameters")    
      with gr.Row():
        gr.Markdown("Picture")
      with gr.Row():
        gr.Image()
      with gr.Row():
        btnSetImage = gr.Button("Set Image")
        btnResetImage = gr.Button("Reset Image")    
    pod.launch(allowed_paths=["."])