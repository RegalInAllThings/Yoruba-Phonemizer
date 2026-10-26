from yorubag2p_prototype import HybridConverter
x=HybridConverter()
for w in ['yorùbá','ọmọ','ǹkan','ń','fẹ́','kọ́']:
    print(w,x.word(w,mode='compare'))
for text in ['Mo fẹ́ kọ́ èdè Yorùbá.','Ọmọ náà ń lọ sí ilé.']:
    print('RULE  ',x.text(text,'rule'))
    print('NEURAL',x.text(text,'neural'))
