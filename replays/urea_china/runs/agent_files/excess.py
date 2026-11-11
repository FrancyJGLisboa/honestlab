import openpyxl, numpy as np, sys
wb=openpyxl.load_workbook(sys.argv[1],read_only=True)
rows=list(wb['Monthly Prices'].iter_rows(values_only=True))[6:]
d={r[0]:(r[60],r[7],r[8]) for r in rows if r[0] and '2015M01'<=r[0]<='2021M12'}
m=sorted(d); U=np.log([d[k][0] for k in m]); G=np.log([[d[k][1],d[k][2]] for k in m])
def X(cols,idx): return np.column_stack([np.ones(len(idx))]+[G[idx,c] for c in cols])
def gap(cols,fit_end,w0,w1):
    fi=np.arange(0,fit_end); wi=np.arange(w0,w1)
    b=np.linalg.lstsq(X(cols,fi),U[fi],rcond=None)[0]
    return float(np.mean(U[wi]-X(cols,wi)@b))   # mean log gap
i=m.index('2021M10')
for name,cols in [('gas EUA+Europa',[0,1]),('gas Europa',[1]),('gas EUA',[0])]:
    g=gap(cols,i,i,i+3)
    pl=[gap(cols,s,s,s+3) for s in range(36,i-2)]   # janelas falsas: fit so com o passado
    pl=np.array(pl)
    print(f"{name}: sobra Out-Dez/21 = {np.expm1(g)*100:.0f}% acima do esperado; "
          f"janelas falsas (n={len(pl)}): mediana {np.expm1(np.median(pl))*100:.0f}%, "
          f"|max| {np.expm1(np.abs(pl).max())*100:.0f}%, acima do real em {np.mean(pl>=g)*100:.0f}% delas")
