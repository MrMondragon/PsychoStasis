import os
import re
import glob
import markdown
import html
from collections import deque
from ContextEntry import ContextEntry
from ShortTermMemory import shortTermMemory
from Nexus import globalNexus
from Logger import globalLogger, LogLevel

cwd = os.getcwd()

#JS loader
workPath = os.path.join(cwd, 'js')
file_list = glob.glob(os.path.join(workPath, 'chat.js'))
for file in file_list:
  with open(file) as f:
      chatScript = f.read()

#CSS loader
workPath = os.path.join(cwd, 'css')
file_list = glob.glob(os.path.join(workPath, 'chatSylte.css'))
filename = file_list[0]
with open(filename) as f:
    chatStyle = f.read()


scrollButton = """// Create the button element
const button = document.createElement('button');
button.textContent = 'Scroll';
button.classList.add('scrollButton');

// Define the scrollToBottom function
function scrollToBottom() {
  const element = document.getElementById('chat');
  if (element) {
    element.scrollTop = element.scrollHeight;
    console.log('scrolled');
  }
  else {
    console.log('element not found');
  }
}

// Attach the click event listener to the button
button.addEventListener('click', scrollToBottom);

// Append the button to the document body (or any other desired location)
document.body.appendChild(button);"""
    
def replace_blockquote(m):
    return m.group().replace('\n', '\n> ').replace('\\begin{blockquote}', '').replace('\\end{blockquote}', '')
    
    
def convert_to_markdown(string):
  
    # Blockquote
    string = re.sub(r'(^|[\n])&gt;', r'\1>', string)
    pattern = re.compile(r'\\begin{blockquote}(.*?)\\end{blockquote}', re.DOTALL)
    string = pattern.sub(replace_blockquote, string)

    # Code
    string = string.replace('\\begin{code}', '```')
    string = string.replace('\\end{code}', '```')
    string = re.sub(r"(.)```", r"\1\n```", string)

    result = ''
    is_code = False
    for line in string.split('\n'):
        if line.lstrip(' ').startswith('```'):
            is_code = not is_code

        result += line
        if is_code or line.startswith('|'):  # Don't add an extra \n for tables or code
            result += '\n'
        else:
            result += '\n\n'

    result = result.strip()
    if is_code:
        result += '\n```'  # Unfinished code block

    # Unfinished list, like "\n1.". A |delete| string is added and then
    # removed to force a <ol> or <ul> to be generated instead of a <p>.
    if re.search(r'(\n\d+\.?|\n\*\s*)$', result):
        delete_str = '|delete|'

        if re.search(r'(\d+\.?)$', result) and not result.endswith('.'):
            result += '.'

        result = re.sub(r'(\n\d+\.?|\n\*\s*)$', r'\g<1> ' + delete_str, result)

        html_output = markdown.markdown(result, extensions=['fenced_code', 'tables'])
        pos = html_output.rfind(delete_str)
        if pos > -1:
            html_output = html_output[:pos] + html_output[pos + len(delete_str):]
    else:
        html_output = markdown.markdown(result, extensions=['fenced_code', 'tables'])

    # Unescape code blocks
    pattern = re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL)
    html_output = pattern.sub(lambda x: html.unescape(x.group()), html_output)

    return html_output    
  
def generateAvatarHTML(roleName: str):
  imagePath= os.path.join(workPath, "assets", f"{roleName}.png")
  if(not os.path.isfile(imagePath)):
    imagePath= os.path.join(workPath, "assets", f"ignore.png")
  
  html = f"""
  <div class='centered-div'>
    <img src='file/{imagePath}' alt='{roleName}'>
  </div>
  """
  return html
  

def generateMessageHTML(message: ContextEntry):
  role = message.role
  content = message.content
  roleName = message.roleName
  
  imagePath= os.path.join(workPath, "assets", f"{roleName}.png")
  if(not os.path.isfile(imagePath)):
    imagePath= os.path.join(workPath, "assets", "ignore.png")    
  imagePath = glob.glob(imagePath)
  if(os.path.isfile(imagePath[0])):
    imagePath = f"<img src='file/{imagePath[0]}' alt='{roleName}'>"
  else:
    imagePath = ""
  
  if(content):
    if(role == "user"):
      template = f'''
                      <div class="message">
                      <div class="circle-you">
                        {imagePath}
                      </div>
                      <div class="text">
                        <div class="username">
                          {roleName}
                        </div>
                        <div class="message-body">
                          {convert_to_markdown(content)}
                        </div>
                      </div>
                    </div>
      '''
    else:
      template = f'''
                    <div class="message">
                    <div class="circle-bot">
                      {imagePath}
                    </div>
                    <div class="text">
                      <div class="username">
                        {roleName}
                      </div>
                      <div class="message-body">
                        {convert_to_markdown(content)}
                      </div>
                    </div>
                  </div>
      '''
    return template
  else:
    return None
  
def generateHTML():
  html = f'<div class="chat" id="chat"><div class="messages">'

  if(globalNexus.ActiveProxy):
    history = deque(globalNexus.ActiveProxy.context.messageHistory)
  else:
    history = deque()
    
  while len(history) > 0:
    message = history.popleft()
    messageHtml = generateMessageHTML(message)
    if(messageHtml):
      html += messageHtml

  html += f'''</div></div>'''
  return html

def sendMessage(message):
  if(message):
    globalNexus.BroadCastMessage(message=message) 
  html = generateHTML()
  if(globalNexus.ActiveCollective is not None):
    proxies = [proxy.name for proxy in globalNexus.ActiveCollective.proxies.values()]
    proxies = "\n".join(proxies)
  else:
    proxies = ""
    
  
  return "", html, globalLogger.GenerateHTML(), globalNexus.ActiveProxy.name, proxies, generateAvatarHTML(globalNexus.ActiveProxy.name), shortTermMemory.GenerateHTML()