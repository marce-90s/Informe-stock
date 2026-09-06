"""Rebuild the portfolio dataset and Power BI import model using only stdlib."""
import calendar
import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'prepared'
MODEL = ROOT / 'Informe stock.SemanticModel' / 'definition'
SEED = 28092017


def read(name):
    with (ROOT / 'archive' / f'{name}.csv').open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (OUT / f'{name}.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    tables = {n: read(n) for n in ['Customer', 'Employee', 'Orders', 'OrderDetails', 'Product', 'Region', 'Warehouse']}
    source_regions = {r['RegionID']: r for r in tables['Region']}
    mapping, locations, warehouses, regions = {}, {}, [], []
    continents = {'United States of America': 'North America', 'Canada': 'North America', 'Mexico': 'North America', 'Australia': 'Oceania', 'China': 'Asia', 'India': 'Asia'}
    for row in tables['Warehouse']:
        key = (row['WarehouseName'], row['WarehouseAddress'])
        if key not in locations:
            ident = len(locations) + 1
            locations[key] = ident
            region = dict(source_regions[row['RegionID']])
            region.update(RegionID=ident, RegionName=continents[region['CountryName']])
            regions.append(region)
            warehouses.append(dict(WarehouseID=ident, WarehouseName=row['WarehouseName'], WarehouseAddress=row['WarehouseAddress'], RegionID=ident))
        mapping[row['WarehouseID']] = locations[key]
    tables['Warehouse'], tables['Region'] = warehouses, regions
    tables['WarehouseMapping'] = [dict(SourceWarehouseID=k, WarehouseID=v) for k, v in mapping.items()]
    for row in tables['Employee']:
        row['SourceWarehouseID'] = row['WarehouseID']
        row['WarehouseID'] = mapping[row['WarehouseID']]
        row['EmployeeHireDate'] = row['EmployeeHireDate'].replace('/', '-')
    for row in tables['Orders']:
        row['OrderDate'] = row['OrderDate'].replace('/', '-')
    # Remove contact information from the published analytical model.
    for name, columns in [('Customer', ['CustomerEmail', 'CustomerPhone', 'CustomerAddress']), ('Employee', ['EmployeeEmail', 'EmployeePhone'])]:
        for row in tables[name]:
            for column in columns:
                del row[column]
    moves, snapshots, current, policies = [], [], [], []
    for product in tables['Product']:
        for wid in sorted(rng.sample(range(1, 10), 3)):
            pid = product['ProductID']
            daily = rng.randint(1, 6)
            lead = rng.randint(3, 14)
            minimum = daily * lead
            target = minimum + daily * 28
            # Scenarios are illustrative supply patterns, not a forecast.
            scenario = rng.choices(['Normal', 'Demora', 'Exceso', 'Sin demanda'], [65, 15, 15, 5])[0]
            balance = rng.randint(minimum, target)
            if scenario == 'Exceso':
                balance = target * 3
            policies.append(dict(ProductID=pid, WarehouseID=wid, LeadTimeDays=lead, MinimumStock=minimum, TargetStock=target, Scenario=scenario))
            def movement(day, kind, quantity):
                moves.append(dict(MovementID=len(moves)+1, Date=day.isoformat(), ProductID=pid, WarehouseID=wid, MovementType=kind, Quantity=quantity, UnitCost=product['ProductStandardCost'], IsSimulated='Yes'))
            movement(date(2017, 1, 1), 'Opening', balance)
            recent = []
            for offset in range(365):
                day = date(2017, 1, 1) + timedelta(days=offset)
                if day.weekday() == 0 and balance < minimum and scenario not in ['Demora', 'Sin demanda']:
                    incoming = target - balance
                    balance += incoming
                    movement(day, 'Receipt', incoming)
                demand = 0 if scenario == 'Sin demanda' else rng.randint(0, daily * 2)
                shipped = min(balance, demand)
                if shipped:
                    balance -= shipped
                    movement(day, 'Issue', -shipped)
                recent.append(shipped)
                if day.day == calendar.monthrange(day.year, day.month)[1]:
                    snapshots.append(dict(Date=day.isoformat(), ProductID=pid, WarehouseID=wid, OnHand=balance, UnitCost=product['ProductStandardCost']))
            reserved = rng.randint(0, min(balance, daily*3))
            available = balance - reserved
            status = 'Sin stock' if available == 0 else 'Bajo minimo' if available < minimum else 'Exceso' if available > target else 'Normal'
            current.append(dict(Date='2017-12-31', ProductID=pid, WarehouseID=wid, OnHand=balance, Reserved=reserved, Available=available, MinimumStock=minimum, TargetStock=target, ReorderQuantity=max(0,target-available) if available<minimum else 0, IssuesLast30Days=sum(recent[-30:]), UnitCost=product['ProductStandardCost'], StockStatus=status))
    tables.update(InventoryMovements=moves, InventoryMonthly=snapshots, InventoryCurrent=current, InventoryPolicy=policies)
    dates = []
    day = date(2013, 1, 1)
    while day <= date(2017, 12, 31):
        dates.append(dict(Date=day.isoformat(), Year=day.year, Month=day.month, MonthName=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][day.month-1], YearMonth=day.strftime('%Y-%m')))
        day += timedelta(days=1)
    tables['Calendario Base'] = dates
    for name, rows in tables.items():
        write(name, rows)
    validate(tables)
    create_model(tables)
    manifest = dict(seed=SEED, simulation_start='2017-01-01', cutoff='2017-12-31', rows={n:len(r) for n,r in tables.items()}, source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'archive').glob('*.csv'))}, totals=dict(on_hand=sum(r['OnHand'] for r in current), reserved=sum(r['Reserved'] for r in current), available=sum(r['Available'] for r in current), inventory_value=round(sum(r['OnHand']*float(r['UnitCost']) for r in current),2)), validation='passed')
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2),encoding='utf-8')
    print(json.dumps(manifest, indent=2))


def validate(tables):
    for table, key in [('Product','ProductID'),('Customer','CustomerID'),('Orders','OrderID'),('OrderDetails','OrderDetailsID'),('Employee','EmployeeID'),('Warehouse','WarehouseID'),('Region','RegionID'),('Calendario Base','Date')]:
        assert len(tables[table]) == len({str(r[key]) for r in tables[table]}), (table,'duplicate key')
    for table, key, parent, parentkey in relations():
        valid = {str(r[parentkey]) for r in tables[parent]}
        assert all(str(r[key]) in valid for r in tables[table]), (table,key,'orphan')
    balances = defaultdict(int)
    expected = {}
    for r in sorted(tables['InventoryMovements'],key=lambda r:(r['Date'],r['MovementID'])):
        key = r['ProductID'],r['WarehouseID']
        balances[key] += r['Quantity']
        assert balances[key] >= 0, ('negative stock',key)
        expected[(key,r['Date'][:7])] = balances[key]
    closing = {}
    for r in sorted(tables['InventoryMonthly'], key=lambda r:r['Date']):
        key = r['ProductID'],r['WarehouseID']
        closing[key] = expected.get((key,r['Date'][:7]),closing.get(key,0))
        assert r['OnHand'] == closing[key], ('monthly reconciliation',r)
    for r in tables['InventoryCurrent']:
        key = r['ProductID'],r['WarehouseID']
        assert r['OnHand'] == balances[key] == closing[key]
        assert 0 <= r['Reserved'] <= r['OnHand']
        assert r['Available'] == r['OnHand']-r['Reserved']
    assert len(tables['InventoryMonthly']) == 12*len(tables['InventoryCurrent'])


def relations():
    rel = [('Orders','CustomerID','Customer','CustomerID'),('OrderDetails','OrderID','Orders','OrderID'),('OrderDetails','ProductID','Product','ProductID'),('Orders','OrderDate','Calendario Base','Date'),('Warehouse','RegionID','Region','RegionID'),('Employee','WarehouseID','Warehouse','WarehouseID'),('WarehouseMapping','WarehouseID','Warehouse','WarehouseID')]
    for t in ['InventoryMovements','InventoryMonthly','InventoryCurrent','InventoryPolicy']:
        rel.extend([(t,'ProductID','Product','ProductID'),(t,'WarehouseID','Warehouse','WarehouseID')])
    # Current is a fixed snapshot, intentionally unaffected by a historical date slicer.
    for t in ['InventoryMovements','InventoryMonthly']:
        rel.append((t,'Date','Calendario Base','Date'))
    return rel


def create_model(tables):
    for name, rows in tables.items():
        lines = [f"table '{name}'"]
        if name == 'WarehouseMapping':
            lines.append('\tisHidden')
        for col in rows[0]:
            vals = [str(r[col]) for r in rows]
            typ = 'string'
            if col in ['Date','OrderDate','EmployeeHireDate']:
                typ = 'dateTime'
            else:
                try:
                    for value in vals: int(value)
                    typ = 'int64'
                except ValueError:
                    try:
                        for value in vals: float(value)
                        typ = 'decimal'
                    except ValueError:
                        pass
            lines.extend([f"\n\tcolumn '{col}'",f'\t\tdataType: {typ}','\t\tsummarizeBy: none',f'\t\tsourceColumn: {col}'])
            if typ == 'dateTime': lines.append('\t\tformatString: Short Date')
            if col == 'MonthName': lines.append('\t\tsortByColumn: Month')
        mtypes = {'string':'type text','int64':'Int64.Type','decimal':'Currency.Type','dateTime':'type date'}
        pairs = []
        for i,line in enumerate(lines):
            if line.lstrip('\n').startswith('\tcolumn '):
                col = line.split("'")[1]
                typ = lines[i+1].split(': ')[1]
                pairs.append('{"'+col+'", '+mtypes[typ]+'}')
        lines.extend([f"\n\tpartition '{name}' = m",'\t\tmode: import','\t\tsource =','\t\t\tlet',f'\t\t\t    Source = Csv.Document(File.Contents(DataRoot & "/{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','\t\t\t    Typed = Table.TransformColumnTypes(Headers, {'+', '.join(pairs)+'}, "en-US")','\t\t\tin Typed',''])
        (MODEL/'tables'/f'{name}.tmdl').write_text('\n'.join(lines),encoding='utf-8')
    (MODEL/'expressions.tmdl').write_text('expression DataRoot = "'+OUT.as_posix()+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n',encoding='utf-8')
    model = 'model Model\n\tculture: es-ES\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n'
    model += '\n'.join(f"ref table '{n}'" for n in [*tables,'Medidas DAX','Actualizado al'])+'\n\nref expression DataRoot\n\nref cultureInfo es-ES\n'
    (MODEL/'model.tmdl').write_text(model,encoding='utf-8')
    rels = []
    for i,(a,ac,b,bc) in enumerate(relations()):
        rels.append(f"relationship rel_{i:02d}\n\tfromColumn: '{a}'.'{ac}'\n\ttoColumn: '{b}'.'{bc}'\n\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n")
    (MODEL/'relationships.tmdl').write_text('\n'.join(rels),encoding='utf-8')
    # Generated auto-date tables are superseded by the shared calendar.
    for p in (MODEL/'tables').glob('*DateTable*.tmdl'):
        p.unlink()


if __name__ == '__main__':
    build()
