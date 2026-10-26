from pathlib import Path
from .converter import YorubaConverter
from .neural import NeuralConverter

class HybridConverter:
    def __init__(self,checkpoint_path=None):
        self.rule=YorubaConverter()
        if checkpoint_path is None:
            checkpoint_path=Path(__file__).resolve().parent.parent/'g2p_silver_model.pt'
        self.neural=NeuralConverter(checkpoint_path)
    def word(self,word,mode='rule'):
        if mode=='rule':return self.rule.word(word)
        if mode=='neural':return self.neural.word(word)
        if mode=='compare':return {'rule':self.rule.word(word),'neural':self.neural.word(word)}
        raise ValueError('mode must be rule, neural, or compare')
    def text(self,text,mode='rule'):
        parts=[]
        for kind,token in self.rule.tokenize(text):
            if kind!='word':parts.append(token);continue
            phones=self.word(token,mode)
            if mode=='compare':parts.append('[rule: '+' '.join(phones['rule'])+' | neural: '+' '.join(phones['neural'])+']')
            else:parts.append('['+' '.join(phones)+']')
        return ''.join(parts)
    def batch(self,texts,mode='rule'):
        return [self.text(text,mode) for text in texts]
