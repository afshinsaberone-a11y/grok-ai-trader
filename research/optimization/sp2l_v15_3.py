"""SP2L v15.3 research state machine: Spike -> Leg-1 pullback -> Leg-2 confirmation.
This is an explicit deterministic research proxy, not a claim of exact reproduction of a proprietary SP2L specification.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Params:
    atr_period:int=14
    spike_atr:float=1.5
    spike_body_ratio:float=0.60
    pullback_min_frac:float=0.25
    pullback_max_frac:float=0.75
    max_pullback_bars:int=3
    confirmation_frac:float=0.50
    expiry_bars:int=8

def signals(df:pd.DataFrame,p:Params=Params())->pd.Series:
    need={'Open','High','Low','Close'}
    if not need.issubset(df.columns): raise ValueError(f'missing columns: {need-set(df.columns)}')
    d=df.sort_index(); tr=pd.concat([d.High-d.Low,(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(p.atr_period,min_periods=p.atr_period).mean()
    out=pd.Series(0,index=d.index,dtype='int8'); state=0; direction=0; hi=lo=size=0.0; pb=age=0; confirm=0.0
    for i in range(p.atr_period,len(d)):
        o,h,l,c=map(float,d.iloc[i][['Open','High','Low','Close']]); a=float(atr.iloc[i])
        if not np.isfinite(a) or a<=0: continue
        rng=h-l; body=abs(c-o); spike=rng>=p.spike_atr*a and rng>0 and body/rng>=p.spike_body_ratio
        if state==0:
            if spike:
                direction=1 if c>o else -1; hi=h; lo=l; size=rng; pb=0; age=0; state=1
            continue
        age+=1
        if age>p.expiry_bars: state=0; direction=0; continue
        pb+=1
        if state==1:
            if pb>p.max_pullback_bars: state=0; direction=0; continue
            retrace=(hi-l)/size if direction==1 else (h-lo)/size
            if retrace>p.pullback_max_frac: state=0; direction=0; continue
            if retrace>=p.pullback_min_frac:
                confirm=lo+p.confirmation_frac*size if direction==1 else hi-p.confirmation_frac*size
                state=2
        if state==2:
            if direction==1 and c>confirm: out.iloc[i]=1; state=0; direction=0
            elif direction==-1 and c<confirm: out.iloc[i]=-1; state=0; direction=0
    return out

def audit(df:pd.DataFrame,p:Params=Params())->dict:
    s=signals(df,p); n=len(s); e=int((s!=0).sum())
    return {'rows':n,'entries':e,'signal_rate_pct':round(100*e/n,4) if n else 0.0,'long_entries':int((s==1).sum()),'short_entries':int((s==-1).sum()),'one_shot_per_setup':True,'future_bar_access':False,'synthetic_data':False}
