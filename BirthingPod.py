import gradio as gr
import re
from Proxy import Proxy
from Nexus import globalNexus, Nexus
from PIL import Image
import grammars
from Logger import globalLogger, LogLevel
import os
import numpy as np


lora_path = 'lora\\' 
imagePath = 'css\\assets\\'
cwd = os.getcwd()


class BirthingPod(object):
  def __init__(self):
    self.activeProxy = None

  def createProxy(self, name, modelName, lora):
    if(modelName):
      modelName = modelName.split(".")[0]
    if(lora):
      workPath = os.path.join(cwd, lora_path)
      workPath = os.path.join(workPath, lora)
      lora = workPath
    self.activeProxy = Proxy(name=name, modelName=modelName, LoRa=lora) 
    globalLogger.log(logLevel=LogLevel.globalLog, message=f"Created proxy {self.activeProxy.name} with model {self.activeProxy.modelName} and lora {self.activeProxy.LoRa}")
    return f"Created proxy {self.activeProxy.name} with model {self.activeProxy.modelName} and lora {self.activeProxy.LoRa}"
    
  def setPrimer(self, primer):
    self.activeProxy.primer = primer
    entry = globalLogger.log(message=f"Primer for proxy {self.activeProxy.name} set", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg
  
  def interrogate(self, prompt):
    self.activeProxy.enterSubContext(copySystem=True)
    try:
      result = self.activeProxy.GenerateAnswer(prompt=prompt)
    finally:
      self.activeProxy.exitSubContext()
    return result.content

  def interrogateTenets(self, prompt):
    self.activeProxy.enterSubContext(copySystem=True)
    try:
      result = self.activeProxy.GenerateAnswer(prompt=prompt, grammar=grammars.list)
    finally:
      self.activeProxy.exitSubContext()
    return result.content

  
  def setTenets(self, tenets):
    tenetList = tenets.splitlines()
    for tenet in tenetList:
      prefix = re.match(r"(\d)*(\.|-|\))\s+", tenet)
      if(prefix):
        prefix = prefix.group()
        tenet = tenet[len(prefix):]
      self.activeProxy.tenets.append(tenet)
    entry = globalLogger.log(message=f"Tenets for proxy {self.activeProxy.name} set", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg


  def setTags(self, tags):
    if(',' in tags):
      tags = tags.split(',')
    elif (';' in tags):
      tags = tags.split(';')
    for tag in tags:
      self.activeProxy.tags.append(tag)
    entry = globalLogger.log(message=f"Tags for proxy {self.activeProxy.name} set", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg
  

  def setParams(self, temperature, person, innerPersona):
    self.activeProxy.temperature = temperature
    self.activeProxy.person = person
    self.activeProxy.innerPersona = innerPersona
    entry = globalLogger.log(message=f"Params for proxy {self.activeProxy.name} set", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg
  
  
  def saveImage(self, image):
    if isinstance(image, np.ndarray):
      image = Image.fromarray(image)
    # Save image as PNG
    workPath = os.path.join(cwd, imagePath)
    workPath = os.path.join(workPath, self.activeProxy.name+'.png')
    image.save(workPath, format="PNG")
    entry = globalLogger.log(message=f"Portrait for proxy {self.activeProxy.name} saved at {workPath}", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg    


  def saveConfigs(self):
    self.activeProxy.SaveConfigs()
    entry = globalLogger.log(message=f"Configurations for proxy {self.activeProxy.name} saved", logLevel=LogLevel.globalLog)
    msg = f"[{entry.logTime}]: {entry.message}"
    return msg    
    

  def Pod(self):
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
        mkdCreateProxy = gr.Markdown("")
        btnCreate.click(self.createProxy, inputs=[txtName, modelSelector, loraSelector], outputs=[mkdCreateProxy])
      with gr.Row():
        txtPrimerPrompt = gr.Textbox(label="Primer", value="Give me a prompt that would define you, your world view. Do not mention your tenets! Start with 'I am a...'")
      with gr.Row():
        txtPrimer = gr.Textbox(label="Primer", lines=2)
      with gr.Row():
        btnInterrogatePrimer = gr.Button("Interrogate Primer")
        btnSetPrimer = gr.Button("Set Primer")
        mkdSetPrimer = gr.Markdown("")
        btnInterrogatePrimer.click(self.interrogate, inputs=[txtPrimerPrompt], outputs=[txtPrimer])
        btnSetPrimer.click(self.setPrimer, inputs=[txtPrimer], outputs = [mkdSetPrimer])
      with gr.Row():
        txtTenetPrompt = gr.Textbox(label="Tenets", value="List at the least four of what you consider your core values, your tenets.")
      with gr.Row():
        btnInterrogateTenet = gr.Button("Interrogate Tenets")
      with gr.Row():
        txtTenet = gr.Textbox(label="Tenet", lines=5)    
        btnInterrogateTenet.click(self.interrogateTenets, inputs=[txtTenetPrompt], outputs=[txtTenet])
      with gr.Row():
        btnSetTenet = gr.Button("Set Tenets")
        mkdSetTenet = gr.Markdown("")
        btnSetTenet.click(self.setTenets, inputs=[txtTenet], outputs = [mkdSetTenet])
      with gr.Row():
        txtTagsPrompt = gr.Textbox(label="Tags", value="Now give me a few (at the least seven) tags that I could use to classfy you. These tags should contain no more than 2 words each and the tags should be separated by commas")
      with gr.Row():
        btnInterrogateTags = gr.Button("Interrogate Tags")
      with gr.Row():
        txtTags = gr.Textbox(label="Tags", lines=1)
        btnInterrogateTags.click(self.interrogate, inputs=[txtTagsPrompt], outputs=[txtTags])
      with gr.Row():
        btnSetTags = gr.Button("Set Tags")
        mkdTags = gr.Markdown("")
        btnSetTags.click(self.setTags, inputs=[txtTags], outputs = [mkdTags])
      with gr.Row():
        gr.Markdown("Parameters")
      with gr.Row():
        sldTemperature = gr.Slider(label="Temperature", value=0.7, maximum=1)
        txtPerson = gr.Dropdown(label="Person", choices=["1st", "3rd"], value="1st")
        txtInnerPersona = gr.Textbox(label="Inner Persona", lines=3, value="These are my private thoughts. Here I will feel free to express my most intimate feelings and desires")
      with gr.Row():
        btnSetParams = gr.Button("Set Parameters")
        mkdSetParams = gr.Markdown("")
        btnSetParams.click(self.setParams, inputs=[sldTemperature, txtPerson, txtInnerPersona], outputs = [mkdSetParams])
      with gr.Row():
        gr.Markdown("Picture")
      with gr.Row():
        imgPicture =gr.Image()
      with gr.Row():
        btnSaveImage = gr.Button("Save Image")
        mkdImage = gr.Markdown("")
        btnSaveImage.click(self.saveImage, inputs=[imgPicture], outputs = [mkdImage])
      with gr.Row():
        btnSaveConfigs = gr.Button("Save Configs")
        mkdConfigs = gr.Markdown("")
        btnSaveConfigs.click(self.saveConfigs, inputs=[], outputs = [mkdConfigs])
    return pod  