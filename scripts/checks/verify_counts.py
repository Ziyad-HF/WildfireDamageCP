import sys, os, pandas as pd
R=sys.argv[1]; C=os.path.join(R,'data/processed/crops'); M=os.path.join(R,'data/metadata')
x=pd.read_csv(f'{C}/index_xbd_v2.csv'); e=pd.read_csv(f'{C}/index_eaton.csv')
bx=pd.read_csv(f'{M}/buildings_xbd.csv'); be=pd.read_csv(f'{M}/buildings_eaton.csv')
print('index_xbd rows',len(x),'cols',list(x.columns)); print('index_eaton rows',len(e),'cols',list(e.columns))
print('buildings_xbd rows',len(bx),'cols',list(bx.columns),'tiles',bx['tile'].nunique()); print('buildings_eaton rows',len(be),'cols',list(be.columns))
for name,d in [('xbd',x),('eaton',e)]:
    print(name,'dup ids',d['id'].duplicated().sum()); print(pd.crosstab(d['fold'],d['label'],margins=True)); print(pd.crosstab(d['event'],d['label']))
    print('label vs orig_label'); print(pd.crosstab(d['orig_label'],d['label']))
print('xbd ids match metadata:', set(x.id)==set(bx.id), ' eaton:', set(e.id)==set(be.id))
oob=((x.bx<0)|(x.bx>223)|(x.by<0)|(x.by>223)).sum(); print('xbd bx/by out of 0-223:',oob, ' eaton:',((e.bx<0)|(e.bx>223)|(e.by<0)|(e.by>223)).sum())
miss=0
for d in (x,e):
    for col in ('pre','post'):
        miss+=sum(not os.path.isfile(os.path.join(C,p)) and not os.path.isfile(os.path.join(R,p)) for p in d[col])
print('missing crop files referenced by index:',miss); print('example paths',x.pre.iloc[0],e.post.iloc[0])
for sub in ('xbd','eaton'):
    print(sub,'jpg files on disk',sum(len([f for f in fs if f.endswith('.jpg')]) for _,_,fs in os.walk(os.path.join(C,sub))))
print(sorted(os.listdir(M)))
