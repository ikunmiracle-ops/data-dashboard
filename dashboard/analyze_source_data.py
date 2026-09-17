# -*- coding: utf-8 -*-
"""对 shop.csv / cpc.csv 做结构画像，为看板取数做准备。"""
import csv, io, os, collections

BASE = r'D:\HuaweiMoveData\Users\25785\Desktop\看板源数据'


def load(name):
    p = os.path.join(BASE, name)
    raw = open(p, 'rb').read()
    for e in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']:
        try:
            text = raw.decode(e)
            break
        except Exception:
            continue
    rows = list(csv.DictReader(io.StringIO(text)))
    return [r for r in rows if any((v or '').strip() for v in r.values())]


def num(v):
    v = (v or '').strip().replace(',', '')
    if v == '':
        return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


shop = load('shop.csv')
cpc = load('cpc.csv')

print('=' * 74)
print('shop.csv  行数 =', len(shop))
print('cpc.csv   行数 =', len(cpc))

for label, rows, datecol in [('shop', shop, '日期'), ('cpc', cpc, '日期')]:
    ds = sorted(set(r[datecol] for r in rows))
    print('-' * 74)
    print('[%s] 日期区间: %s ~ %s   (共 %d 个不同日期)' % (label, ds[0], ds[-1], len(ds)))

print('-' * 74)
print('[shop] 品牌:', sorted(set(r['品牌名称'] for r in shop)))
print('[shop] 品牌id:', sorted(set(r['品牌id'] for r in shop)))
print('[shop] 门店数:', len(set(r['门店id'] for r in shop)))
print('[shop] 城市:', sorted(set(r['城市'] for r in shop)))
print('[shop] 平台:', sorted(set(r['平台'] for r in shop)))
print('[cpc ] 品牌id:', sorted(set(r['品牌id'] for r in cpc)))
print('[cpc ] 门店数:', len(set(r['门店id'] for r in cpc)))
print('[cpc ] 门店id 列表:', sorted(set(r['门店id'] for r in cpc)))

# 粒度检查：shop 是否 日期+门店+平台 唯一
k1 = collections.Counter((r['日期'], r['门店id'], r['平台']) for r in shop)
k2 = collections.Counter((r['日期'], r['门店id']) for r in cpc)
print('-' * 74)
print('[shop] 日期+门店+平台 唯一性: 总行 %d, 组合 %d, 重复组 %d'
      % (len(shop), len(k1), sum(1 for v in k1.values() if v > 1)))
print('[cpc ] 日期+门店 唯一性:      总行 %d, 组合 %d, 重复组 %d'
      % (len(cpc), len(k2), sum(1 for v in k2.values() if v > 1)))

# 关联率：cpc 的 日期+门店 有多少能在 shop 里找到
shopStoreDate = set((r['日期'], r['门店id']) for r in shop)
cpcKeys = set((r['日期'], r['门店id']) for r in cpc)
matched = len(cpcKeys & shopStoreDate)
print('-' * 74)
print('cpc 的 日期+门店 组合数 = %d, 能匹配到 shop 的 = %d (%.1f%%)'
      % (len(cpcKeys), matched, matched * 100.0 / max(1, len(cpcKeys))))
print('shop 的 日期+门店 组合数 = %d' % len(shopStoreDate))

# 日期交集
shopDates = set(r['日期'] for r in shop)
cpcDates = set(r['日期'] for r in cpc)
inter = sorted(shopDates & cpcDates)
print('日期交集: %d 天, %s ~ %s' % (len(inter), inter[0] if inter else '-', inter[-1] if inter else '-'))
print('仅 shop 有: %d 天 / 仅 cpc 有: %d 天' % (len(shopDates - cpcDates), len(cpcDates - shopDates)))

# 口径验证：把 shop 聚合到 门店+日期，比较进店/曝光 与 cpc
agg = collections.defaultdict(lambda: {'visit': 0.0, 'exp': 0.0, 'gmv': 0.0})
for r in shop:
    a = agg[(r['日期'], r['门店id'])]
    a['visit'] += num(r['进店人数'])
    a['exp'] += num(r['曝光人数'])
    a['gmv'] += num(r['GMV'])

cVisitLt = cVisitGt = 0
ratio = []
for r in cpc:
    k = (r['日期'], r['门店id'])
    if k not in agg:
        continue
    cv = num(r['cpc进店人数'])
    sv = agg[k]['visit']
    if sv <= 0:
        continue
    ratio.append(cv / sv)
    if cv <= sv:
        cVisitLt += 1
    else:
        cVisitGt += 1
print('-' * 74)
print('[口径] cpc进店人数 <= shop进店人数(同店同日) 的比例: %d / %d' % (cVisitLt, cVisitLt + cVisitGt))
if ratio:
    ratio.sort()
    print('[口径] cpc进店/shop进店 比值: 最小 %.3f  中位 %.3f  最大 %.3f'
          % (ratio[0], ratio[len(ratio) // 2], ratio[-1]))

# 字段基本统计
print('-' * 74)
print('[shop] 关键字段合计与均值:')
fields = ['GMV', '商家实收', '商家补贴', '平台补贴', '曝光人数', '进店人数', '下单人数', '有效订单数', '无效订单数']
tot = {}
for f in fields:
    vals = [num(r[f]) for r in shop]
    tot[f] = sum(vals)
    nz = sum(1 for v in vals if v == 0)
    neg = sum(1 for v in vals if v < 0)
    print('  %-8s 合计=%-16.0f 均值=%-12.1f 零值=%-5d 负值=%d' % (f, sum(vals), sum(vals) / len(vals), nz, neg))

print('[cpc ] 关键字段合计与均值:')
for f in ['cpc总费用', 'cpc曝光人数', 'cpc进店人数']:
    vals = [num(r[f]) for r in cpc]
    nz = sum(1 for v in vals if v == 0)
    print('  %-12s 合计=%-16.1f 均值=%-12.1f 零值=%d' % (f, sum(vals), sum(vals) / len(vals), nz))

# 派生比率
print('-' * 74)
gmv, income = tot['GMV'], tot['商家实收']
exp, vis, ordr = tot['曝光人数'], tot['进店人数'], tot['下单人数']
val, inv = tot['有效订单数'], tot['无效订单数']
print('整体实收率 = %.1f%%' % (income / gmv * 100))
print('整体补贴率 = %.1f%%  (商家 %.1f%% + 平台 %.1f%%)'
      % ((tot['商家补贴'] + tot['平台补贴']) / gmv * 100,
         tot['商家补贴'] / gmv * 100, tot['平台补贴'] / gmv * 100))
print('进店率 = %.2f%%   下单率 = %.2f%%   有效率 = %.1f%%'
      % (vis / exp * 100, ordr / vis * 100, val / (val + inv) * 100))
print('客单价 = %.1f 元 (GMV / 有效订单)' % (gmv / val if val else 0))
cost = sum(num(r['cpc总费用']) for r in cpc)
cvis = sum(num(r['cpc进店人数']) for r in cpc)
print('CPC 总费用 = %.0f   到店成本 = %.2f 元   全店投产比 = %.2f' % (cost, cost / cvis if cvis else 0, gmv / cost if cost else 0))
