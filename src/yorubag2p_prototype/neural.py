import unicodedata
from pathlib import Path
import torch
from torch import nn

class Model(nn.Module):
    def __init__(self, nc, np_, hidden=128):
        super().__init__()
        self.ce=nn.Embedding(nc,64,padding_idx=0)
        self.pe=nn.Embedding(np_,64,padding_idx=0)
        self.enc=nn.GRU(64,hidden,batch_first=True,bidirectional=True)
        self.init=nn.Linear(hidden*2,hidden)
        self.attn_query=nn.Linear(hidden,hidden*2,bias=False)
        self.dec=nn.GRUCell(64+hidden*2,hidden)
        self.out=nn.Linear(hidden+hidden*2,np_)
    def encode(self,x):
        memory,h=self.enc(self.ce(x))
        state=torch.tanh(self.init(torch.cat([h[-2],h[-1]],dim=-1)))
        return memory,state,x.ne(0)
    def step(self,tok,state,memory,mask):
        score=torch.bmm(memory,self.attn_query(state).unsqueeze(-1)).squeeze(-1)
        score=score.masked_fill(~mask,-1e9)
        attn=torch.softmax(score,dim=1)
        context=torch.bmm(attn.unsqueeze(1),memory).squeeze(1)
        state=self.dec(torch.cat([self.pe(tok),context],dim=-1),state)
        return self.out(torch.cat([state,context],dim=-1)),state

class NeuralConverter:
    def __init__(self, checkpoint_path):
        try:
            checkpoint=torch.load(str(checkpoint_path),map_location='cpu',weights_only=True)
        except TypeError:
            checkpoint=torch.load(str(checkpoint_path),map_location='cpu')
        self.chars=checkpoint['char_vocab']
        self.phones=checkpoint['phone_vocab']
        self.ci={x:i for i,x in enumerate(self.chars)}
        self.pi={x:i for i,x in enumerate(self.phones)}
        self.model=Model(len(self.chars),len(self.phones),checkpoint['hidden'])
        self.model.load_state_dict(checkpoint['model'],strict=True)
        self.model.eval()
    @torch.inference_mode()
    def word(self,word,max_steps=60):
        word=unicodedata.normalize('NFC',str(word).lower())
        if word=='ń':return ['n_H']
        if word=='ǹ':return ['n_L']
        x=torch.tensor([[self.ci['<bos>']]+[self.ci.get(ch,self.ci['<unk>']) for ch in word]+[self.ci['<eos>']]])
        memory,state,mask=self.model.encode(x)
        tok=torch.tensor([self.pi['<bos>']])
        result=[]
        for _ in range(max_steps):
            logits,state=self.model.step(tok,state,memory,mask)
            tok=logits.argmax(-1)
            idx=int(tok.item())
            if idx==self.pi['<eos>']:break
            if idx not in (self.pi['<pad>'],self.pi['<bos>']):result.append(self.phones[idx])
        return result
