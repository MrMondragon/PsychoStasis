import sys
from pathlib import Path
import torch
sys.path.insert(0, str(Path(".")))


from transformers import (
    DistilBertModel,
    DistilBertForMaskedLM,
    DistilBertForTokenClassification,
    DistilBertForSequenceClassification,
    DistilBertForQuestionAnswering,
    DistilBertTokenizer
)

from transformers import (
    BertModel,
    BertForMaskedLM,
    BertForTokenClassification,
    BertForSequenceClassification,
    BertForQuestionAnswering,
    BertTokenizer
)

from transformers import (
    XLNetModel,
    XLNetForTokenClassification,
    XLNetForSequenceClassification,
    XLNetForQuestionAnswering,
    XLNetTokenizer
)

from Base_model import Base_model

supported_tasks = ["base", "masked_lm", "token_classification", "question_answering", 
                   "sequence_classification", "multiple_choice"]

distilbert_task_mapping = {
    "base": DistilBertModel,
    "masked_lm": DistilBertForMaskedLM,
    "token_classification": DistilBertForTokenClassification,
    "question_answering": DistilBertForQuestionAnswering,
    "sequence_classification": DistilBertForSequenceClassification,
    }

bert_task_mapping = {
    "base": BertModel,
    "masked_lm": BertForMaskedLM,
    "token_classification": BertForTokenClassification,
    "question_answering": BertForQuestionAnswering,
    "sequence_classification": BertForSequenceClassification,
    }

xnl_task_mapping = {
    "base": XLNetModel,
    "token_classification": XLNetForTokenClassification,
    "question_answering": XLNetForQuestionAnswering,
    "sequence_classification": XLNetForSequenceClassification,
    }

model_mapping = {
    "xnl": xnl_task_mapping,
    "bert": bert_task_mapping,
    "distilbert": distilbert_task_mapping    
}

tokenizer_mapping = {
    "xnl": XLNetTokenizer,
    "bert": BertTokenizer,
    "distilbert": DistilBertTokenizer
}



###TODO - COMBINE THE PIPELINE MODELS, IMPLEMENT SPECIALIZED PREDICTIONS AND CREATE A GENERATE METHOD
###AGGREGATING THE PREDICTORS

class Shard_model(Base_model):
    def __init__(self, model_name, **kwargs) -> None:
        super().__init__(model_name, **kwargs) 
        self.task:str  = 'base' if 'task' not in self.params else self.params['task']
        

    def load(self):
        
        taskMapping = model_mapping.get(self.params['model_type'])
        taskClass = taskMapping.get(self.task)
        if(not taskClass):
            raise ValueError(f"Invalid task: {self.task}. Supported tasks: {', '.join(taskMapping.keys())}") 
        # Load the model
        self.model = taskClass.from_pretrained(self.path, kwargs=self.kwargs)
        tokenizerClass = tokenizer_mapping.get(self.params['model_type'])
        # Load the tokenizer
        self.tokenizer = tokenizerClass.from_pretrained(self.path)

    def generate(self, localContext, callback=None):
        super.generate(localContext, callback)

        inputs = self.tokenizer(localContext, return_tensors="pt")
        outputs = self.model(**inputs)
        # Output has shape [batch_size, sequence_length, hidden_size]
        embeddings = outputs[0] 
        text = self.tokenizer.decode(torch.argmax(embeddings[0], dim=1), skip_special_tokens=True)      
        
        if callback:
            callback(text)
        
        return text