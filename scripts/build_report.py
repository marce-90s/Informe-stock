"""Create a compact, reproducible PBIR report and its DAX measures."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'Informe stock.SemanticModel'/'definition'
PAGES = ROOT/'Informe stock.Report'/'definition'/'pages'
MEASURES = {
    'Stock fisico': 'SUM(InventoryCurrent[OnHand])',
    'Stock reservado': 'SUM(InventoryCurrent[Reserved])',
    'Stock disponible': 'SUM(InventoryCurrent[Available])',
    'Valor inventario UM': 'SUMX(InventoryCurrent, InventoryCurrent[OnHand] * InventoryCurrent[UnitCost])',
    'SKU activos': 'DISTINCTCOUNT(InventoryCurrent[ProductID])',
    'Posiciones sin stock': 'CALCULATE(COUNTROWS(InventoryCurrent), KEEPFILTERS(InventoryCurrent[Available] = 0))',
    'Posiciones bajo minimo': 'COUNTROWS(FILTER(InventoryCurrent, InventoryCurrent[Available] < InventoryCurrent[MinimumStock]))',
    'Unidades a reponer': 'SUM(InventoryCurrent[ReorderQuantity])',
    'Cobertura dias': 'DIVIDE([Stock disponible], DIVIDE(SUM(InventoryCurrent[IssuesLast30Days]), 30))',
    'Saldo movimientos': 'SUM(InventoryMovements[Quantity])',
    'Salidas simuladas': '-CALCULATE(SUM(InventoryMovements[Quantity]), InventoryMovements[MovementType] = "Issue")',
    'Entradas simuladas': 'CALCULATE(SUM(InventoryMovements[Quantity]), InventoryMovements[MovementType] = "Receipt")',
    'Stock cierre mensual': 'VAR Corte = MAX(InventoryMonthly[Date]) RETURN CALCULATE(SUM(InventoryMonthly[OnHand]), KEEPFILTERS(InventoryMonthly[Date] = Corte))',
    'Control conciliacion': '[Stock fisico] - CALCULATE([Saldo movimientos], REMOVEFILTERS(\'Calendario Base\'), REMOVEFILTERS(InventoryMovements[MovementType]))',
    'Pedidos historicos': 'COUNTROWS(Orders)',
    'Unidades enviadas historicas': 'CALCULATE(SUM(OrderDetails[OrderItemQuantity]), OrderDetails[OrderStatus] = "Shipped")',
    'Importe enviado historico UM': 'CALCULATE(SUMX(OrderDetails, OrderDetails[OrderItemQuantity] * OrderDetails[PerUnitPrice]), OrderDetails[OrderStatus] = "Shipped")',
}


def dump(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def literal(value):
    return {'expr':{'Literal':{'Value':value}}}


def projection(table, column, measure=False):
    return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}},'queryRef':table+'.'+column,'nativeQueryRef':column}


def visual(page, name, typ, x, y, w, h, title, roles=None, objects=None):
    v = {'visualType':typ,'visualContainerObjects':{'title':[{'properties':{'show':literal('true'),'text':literal("'"+title+"'"),'fontSize':literal('12D')}}]},'drillFilterOtherVisuals':True}
    if roles:
        v['query']={'queryState':{k:{'projections':p} for k,p in roles.items()}}
    if objects:
        v['objects']=objects
    dump(PAGES/page/'visuals'/name/'visual.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.8.0/schema.json','name':name,'position':{'x':x,'y':y,'z':0,'width':w,'height':h,'tabOrder':0},'visual':v})


def text(page,name,text,y,size=16):
    visual(page,name,'textbox',24,y,1230,52,'',objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontSize':str(size)+'pt','fontFamily':'Segoe UI'}}]}]}}]})


def card(page,name,measure,x,title=None):
    visual(page,name,'card',x,130,235,105,title or measure,{'Values':[projection('Medidas DAX',measure,True)]})


def main():
    tmdl = "table 'Medidas DAX'\n"
    for name,expression in MEASURES.items():
        fmt = '#,##0.00' if 'UM' in name else '#,##0.0' if name=='Cobertura dias' else '#,##0'
        tmdl += f"\n\tmeasure '{name}' = {expression}\n\t\tformatString: {fmt}\n"
    tmdl += "\n\tpartition 'Medidas DAX' = m\n\t\tmode: import\n\t\tsource = #table(type table [Placeholder = text], {})\n"
    (MODEL/'tables'/'Medidas DAX.tmdl').write_text(tmdl,encoding='utf-8')
    path=MODEL/'tables'/'Actualizado al.tmdl'
    path.write_text(path.read_text(encoding='utf-8').replace('dataType: string','dataType: dateTime'),encoding='utf-8')
    # Retain the user's BASE page as a hidden template; new pages are separate.
    base=PAGES/'3c978ae384d763d39147'/'page.json'
    page=json.loads(base.read_text(encoding='utf-8'))
    page['visibility']='HiddenInViewMode'
    dump(base,page)
    pages=[('stock_overview','01 | Stock al cierre'),('stock_evolution','02 | Movimientos'),('stock_orders','03 | Pedidos originales')]
    for ident,title in pages:
        dump(PAGES/ident/'page.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json','name':ident,'displayName':title,'displayOption':'FitToPage','height':720,'width':1280})
    p='stock_overview'
    text(p,'heading','INVENTARIO | Disponibilidad y reposición',12,23)
    text(p,'subtitle','CASO SIMULADO · Corte fijo: 31/12/2017 · Valores en unidades monetarias (UM)',62,11)
    for i,m in enumerate(['Stock fisico','Stock disponible','Valor inventario UM','Posiciones bajo minimo','Unidades a reponer']):
        card(p,'kpi'+str(i),m,24+i*250)
    visual(p,'category','slicer',24,250,230,150,'Categoría',{'Values':[projection('Product','CategoryName')]})
    visual(p,'warehouse','slicer',24,410,230,200,'Depósito',{'Values':[projection('Warehouse','WarehouseName')]})
    visual(p,'by_category','clusteredBarChart',280,250,470,270,'Stock disponible por categoría',{'Category':[projection('Product','CategoryName')],'Y':[projection('Medidas DAX','Stock disponible',True)]})
    visual(p,'by_status','tableEx',775,250,480,270,'Estado por posición producto / depósito',{'Values':[projection('InventoryCurrent','StockStatus'),projection('Medidas DAX','Stock fisico',True),projection('Medidas DAX','Unidades a reponer',True)]})
    visual(p,'detail','tableEx',280,535,975,170,'Detalle por depósito',{'Values':[projection('Warehouse','WarehouseName'),projection('Medidas DAX','Stock disponible',True),projection('Medidas DAX','Posiciones sin stock',True),projection('Medidas DAX','Unidades a reponer',True)]})
    p='stock_evolution'
    text(p,'heading','INVENTARIO | Evolución mensual',12,23)
    text(p,'subtitle','CASO SIMULADO · Enero a diciembre de 2017 · Entradas y salidas independientes de pedidos originales',62,11)
    for i,m in enumerate(['Entradas simuladas','Salidas simuladas','Stock cierre mensual','Control conciliacion']):
        card(p,'kpi'+str(i),m,24+i*310)
    visual(p,'category','slicer',24,250,230,160,'Categoría',{'Values':[projection('Product','CategoryName')]})
    visual(p,'warehouse','slicer',24,425,230,240,'Depósito',{'Values':[projection('Warehouse','WarehouseName')]})
    visual(p,'trend','lineChart',280,250,975,280,'Stock al último cierre mensual',{'Category':[projection('Calendario Base','YearMonth')],'Y':[projection('Medidas DAX','Stock cierre mensual',True)]})
    visual(p,'flows','clusteredColumnChart',280,545,975,160,'Flujos simulados por mes',{'Category':[projection('Calendario Base','YearMonth')],'Y':[projection('Medidas DAX','Entradas simuladas',True),projection('Medidas DAX','Salidas simuladas',True)]})
    p='stock_orders'
    text(p,'heading','PEDIDOS | Datos originales',12,23)
    text(p,'subtitle','2013–2017 · Sin vínculo operativo con el inventario simulado · Enviado no equivale a facturado',62,11)
    for i,m in enumerate(['Pedidos historicos','Unidades enviadas historicas','Importe enviado historico UM']):
        card(p,'kpi'+str(i),m,24+i*410)
    visual(p,'year','slicer',24,250,230,180,'Año',{'Values':[projection('Calendario Base','Year')]})
    visual(p,'amount','clusteredColumnChart',280,250,975,280,'Importe de pedidos enviados por año',{'Category':[projection('Calendario Base','Year')],'Y':[projection('Medidas DAX','Importe enviado historico UM',True)]})
    visual(p,'details','tableEx',280,545,975,160,'Detalle original',{'Values':[projection('OrderDetails','OrderID'),projection('OrderDetails','ProductID'),projection('OrderDetails','OrderStatus'),projection('OrderDetails','OrderItemQuantity'),projection('OrderDetails','PerUnitPrice')]})
    dump(PAGES/'pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages]+['3c978ae384d763d39147'],'activePageName':'stock_overview'})
    print('17 measures and 3 report pages generated.')


if __name__=='__main__':
    main()
