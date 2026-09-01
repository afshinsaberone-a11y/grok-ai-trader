"""SP2L v15.7 explicit Spike -> Leg-1 pullback -> Leg-2 confirmation.
Research proxy, not exact proprietary reproduction. No future-bar access.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Params:
    atr_period:int=14
    spike_atr:float=1.5
    spike_body_ratio:float=.60
    pullback_min_frac:float=.25
    pullback_max_frac:float=.75
    max_pullback_bars:int=3
    confirmation_frac:float=.50
    expiry_bars:int=8

def signals(df:pd.DataFrame,p:Params=Params())->pd.Series:
    need={'Open','High','Low','Close'}
    if not need.issubset(df.columns): raise ValueError(f'missing columns: {need-set(df.columns)}')
    d=df.sort_index(); h=d.High.to_numpy(float); l=d.Low.to_numpy(float); o=d.Open.to_numpy(float); c=d.Close.to_numpy(float)
    tr=np.maximum(h-l,np.maximum(np.abs(h-np.r_[np.nan,c[:-1]]),np.abs(l-np.r_[np.nan,c[:-1]])))
    atr=pd.Series(tr,index=d.index).rolling(p.atr_period,min_periods=p.atr_period).mean().to_numpy()
    out=np.zeros(len(d),dtype=np.int8); state=0; direction=0; hi=lo=size=0.; pb=age=0; confirm=0.
    for i in range(p.atr_period,len(d)):
        a=atr[i]; rng=h[i]-l[i]; body=abs(c[i]-o[i])
        if not np.isfinite(a) or a<=0: continue
        if state==0:
            if rng>=p.spike_atr*a and rng>0 and body/rng>=p.spike_body_ratio and c[i]!=o[i]:
                direction=1 if c[i]>o[i] else -1; hi=h[i]; lo=l[i]; size=rng; pb=0; age=0; state=1
            continue
        age+=1
        if age>p.expiry_bars: state=0; direction=0; continue
        if state==1:
            pb+=1
            if pb>p.max_pullback_bars: state=0; direction=0; continue
            retr=(hi-l[i])/size if direction==1 else (h[i]-lo)/size
            if retr>p.pullback_max_frac: state=0; direction=0; continue
            if retr>=p.pullback_min_frac:
                confirm=lo+p.confirmation_frac*size if direction==1 else hi-p.confirmation_frac*size
                state=2
            continue
        if direction==1 and c[i]>confirm: out[i]=1; state=direction=0
        elif direction==-1 and c[i]<confirm: out[i]=-1; state=direction=0
    return pd.Series(out,index=d.index,dtype='int8')

def audit(df,p=Params()):
    s=signals(df,p); n=len(s); e=int((s!=0).sum())
    return {'rows':n,'entries':e,'signal_rate_pct':round(100*e/n,4) if n else 0.,'long_entries':int((s==1).sum()),'short_entries':int((s==-1).sum()),'one_shot_per_setup':True,'future_bar_access':False,'synthetic_data':False}
