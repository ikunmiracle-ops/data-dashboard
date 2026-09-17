# -*- coding: utf-8 -*-
"""把 shop.csv / cpc.csv 转成看板可直接消费的紧凑 JSON。

关键处理：
1. 门店id 是「平台内店铺id」，不是全局门店id —— 门店实体键用「门店名称」。
2. cpc.csv 没有平台字段，用 shop.csv 反查门店id → (门店, 平台)。
3. cpc 是门店级、shop 是 门店×平台 级，统一到 (日期, 门店, 平台) 后拼接。
4. 日期统一为 YYYY-MM-DD。
"""
import csv, io, os, json, collections, datetime

BASE = r'D:\HuaweiMoveData\Users\25785\Desktop\看板源数据'
OUT = r'C:\Users\25785\WorkBuddy\2026-09-15-16-50-57\dashboard-data.js'


def load(name):
    raw = open(os.path.join(BASE, name), 'rb').read()
    for e in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']:
        try:
            text = raw.decode(e)
            break
        except Exception:
            continue
    return [r for r in csv.DictReader(io.StringIO(text))
            if any((v or '').strip() for v in r.values())]


def num(v):
    v = (v or '').strip().replace(',', '')
    if v == '':
        return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


def pd_(s):
    y, m, d = [int(x) for x in s.strip().split('/')]
    return datetime.date(y, m, d)


shop = load('shop.csv')
cpc = load('cpc.csv')

# ---- 门店id -> (门店名, 品牌, 平台) ----
id2sp = {}
for r in shop:
    id2sp[r['门店id']] = (r['门店名称'], r['品牌名称'], r['平台'])

# ---- 门店表（按门店名称聚合） ----
store_info = {}
for r in shop:
    nm = r['门店名称']
    s = store_info.setdefault(nm, {'name': nm, 'brand': r['品牌名称'], 'ids': {}, 'dates': set()})
    s['ids'][r['平台']] = r['门店id']
    s['dates'].add(pd_(r['日期']))

PLATFORMS = ['饿了么', '美团']
BRANDS = sorted(set(r['品牌名称'] for r in shop))

stores = []
for nm in sorted(store_info, key=lambda x: -len(store_info[x]['dates'])):
    s = store_info[nm]
    ds = sorted(s['dates'])
    stores.append({
        'name': nm, 'brand': s['brand'],
        'ids': {p: s['ids'].get(p, '') for p in PLATFORMS},
        'first': ds[0].isoformat(), 'last': ds[-1].isoformat(),
        'days': len(ds),
    })
store_idx = {s['name']: i for i, s in enumerate(stores)}

# ---- 日期轴 ----
alld = set(pd_(r['日期']) for r in shop) | set(pd_(r['日期']) for r in cpc)
dates = sorted(alld)
date_idx = {d: i for i, d in enumerate(dates)}

# ---- shop 行 ----
shop_rows = []
for r in shop:
    shop_rows.append([
        date_idx[pd_(r['日期'])], store_idx[r['门店名称']], PLATFORMS.index(r['平台']),
        int(num(r['GMV'])), int(num(r['商家实收'])), int(num(r['商家补贴'])), int(num(r['平台补贴'])),
        int(num(r['曝光人数'])), int(num(r['进店人数'])), int(num(r['下单人数'])),
        int(num(r['有效订单数'])), int(num(r['无效订单数'])),
    ])
shop_rows.sort(key=lambda x: (x[0], x[1], x[2]))

# ---- cpc 行（用门店id 反查门店与平台） ----
cpc_rows = []
cpc_unmatched = 0
for r in cpc:
    key = id2sp.get(r['门店id'])
    if not key:
        cpc_unmatched += 1
        continue
    nm, brand, plat = key
    cpc_rows.append([
        date_idx[pd_(r['日期'])], store_idx[nm], PLATFORMS.index(plat),
        round(num(r['cpc总费用']), 2), int(num(r['cpc曝光人数'])), int(num(r['cpc进店人数'])),
    ])
cpc_rows.sort(key=lambda x: (x[0], x[1], x[2]))

payload = {
    'generatedAt': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    'source': 'shop.csv %d 行 + cpc.csv %d 行' % (len(shop), len(cpc)),
    'brands': BRANDS,
    'platforms': PLATFORMS,
    'stores': stores,
    'dates': [d.isoformat() for d in dates],
    'shop': shop_rows,
    'cpc': cpc_rows,
}
# cpc 行可关联率
print('cpc 未能映射到门店的行数 =', cpc_unmatched)
print('门店数 =', len(stores), ' 日期轴 =', len(dates), ' shop行 =', len(shop_rows), ' cpc行 =', len(cpc_rows))

js = 'window.DASH_DATA = ' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n'
open(OUT, 'w', encoding='utf-8').write(js)
print('已写出 %s  (%.1f KB)' % (OUT, len(js.encode('utf-8')) / 1024.0))

# ---- 校验：真实汇总 ----
gmv = sum(r[3] for r in shop_rows)
inc = sum(r[4] for r in shop_rows)
ms = sum(r[5] for r in shop_rows)
ps = sum(r[6] for r in shop_rows)
exp = sum(r[7] for r in shop_rows)
vis = sum(r[8] for r in shop_rows)
odr = sum(r[9] for r in shop_rows)
val = sum(r[10] for r in shop_rows)
inv = sum(r[11] for r in shop_rows)
cost = sum(r[3] for r in cpc_rows)
cvis = sum(r[5] for r in cpc_rows)
print('-' * 60)
print('GMV=%.0f 实收=%.0f(%.1f%%) 补贴=%.0f(%.1f%%)' % (gmv, inc, inc / gmv * 100, ms + ps, (ms + ps) / gmv * 100))
print('曝光=%.0f 进店=%.0f(%.2f%%) 下单=%.0f(%.2f%%) 有效订单=%.0f 无效=%d' %
      (exp, vis, vis / exp * 100, odr, odr / vis * 100, val, inv))
print('客单价=%.1f  CPC费用=%.0f  到店成本=%.2f  全店投产比=%.2f' %
      (gmv / val, cost, cost / cvis, gmv / cost))
print('cpc进店 / shop进店 = %.1f%%' % (cvis / vis * 100))
