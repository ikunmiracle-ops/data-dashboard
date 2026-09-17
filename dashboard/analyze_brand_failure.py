# -*- coding: utf-8 -*-
"""品牌失败复盘分析：品牌 -> 平台 -> 门店 三级下钻。

重点回答：
1. 蛙小辣 / 拌客 各自的生命周期与规模曲线
2. 每家门店的存活时长、经营质量、关店前的征兆
3. 关店潮的时间分布，与 2020 年疫情的真实关系
4. 失败路径归因：是补贴依赖、单店模型不成立，还是外部冲击
"""
import json, io, os, collections, datetime, statistics

BASE = r'C:\Users\25785\WorkBuddy\2026-09-15-16-50-57'
s = io.open(os.path.join(BASE, 'dashboard-data.js'), encoding='utf-8').read()
d = json.loads(s[s.index('{'):s.rindex('}') + 1])

DATES = d['dates']
STORES = d['stores']
PLATFORMS = d['platforms']
BRANDS = d['brands']
SHOP = d['shop']   # [di, si, pi, gmv, income, msub, psub, exp, visit, order, valid, invalid]
CPC = d['cpc']     # [di, si, pi, cost, cexp, cvisit]

def pdate(x):
    return datetime.date(*[int(v) for v in x.split('-')])

# 月键
def mk(di):
    return DATES[di][:7]

print('=' * 78)
print('【0】数据基本面')
print('=' * 78)
print('日期区间: %s ~ %s (%d 个有数据日)' % (DATES[0], DATES[-1], len(DATES)))
print('品牌: %s' % BRANDS)
print('平台: %s' % PLATFORMS)
print('门店数: %d' % len(STORES))
print('shop 行 %d / cpc 行 %d' % (len(SHOP), len(CPC)))

# ---------------- 品牌级汇总 ----------------
print()
print('=' * 78)
print('【1】品牌级：蛙小辣 vs 拌客')
print('=' * 78)
for b in BRANDS:
    sis = [i for i, st in enumerate(STORES) if st['brand'] == b]
    rows = [r for r in SHOP if r[1] in sis]
    if not rows:
        continue
    gmv = sum(r[3] for r in rows)
    inc = sum(r[4] for r in rows)
    msub = sum(r[5] for r in rows)
    psub = sum(r[6] for r in rows)
    exp = sum(r[7] for r in rows)
    vis = sum(r[8] for r in rows)
    odr = sum(r[9] for r in rows)
    val = sum(r[10] for r in rows)
    inv = sum(r[11] for r in rows)
    ds = sorted(set(r[0] for r in rows))
    cris = [r for r in CPC if r[1] in sis]
    cost = sum(r[3] for r in cris)
    cvis = sum(r[5] for r in cris)
    print('【%s】' % b)
    print('   在营门店 %d 家 | 数据跨度 %s ~ %s (%d 天有数据)' % (len(sis), DATES[ds[0]], DATES[ds[-1]], len(ds)))
    print('   GMV ¥%.0f | 商家实收 ¥%.0f (%.1f%%)' % (gmv, inc, inc / gmv * 100))
    print('   补贴 ¥%.0f (%.1f%%)  其中商家 ¥%.0f (%.1f%%) / 平台 ¥%.0f (%.1f%%)' % (
        msub + psub, (msub + psub) / gmv * 100, msub, msub / gmv * 100, psub, psub / gmv * 100))
    print('   佣金率 %.2f%% | 曝光 %d | 进店率 %.2f%% | 下单率 %.2f%% | 客单价 ¥%.1f' % (
        (gmv - inc - msub - psub) / gmv * 100, exp, vis / exp * 100, odr / vis * 100, gmv / val))
    print('   有效订单 %d | 无效 %d (无效率 %.2f%%)' % (val, inv, inv / (val + inv) * 100))
    if cost:
        print('   CPC 费用 ¥%.0f | 到店成本 ¥%.2f | 付费进店占比 %.1f%%' % (
            cost, cost / cvis if cvis else 0, cvis / vis * 100))
    print()

# ---------------- 门店级明细 ----------------
print('=' * 78)
print('【2】门店级：存活时长与经营质量')
print('=' * 78)
print('%-22s %-5s %5s %6s %10s %8s %8s %8s %8s' % (
    '门店', '品牌', '存活天', '日历天', 'GMV', '实收率', '补贴率', '客单价', '进店率'))
print('-' * 78)

store_stat = []
for i, st in enumerate(STORES):
    rows = [r for r in SHOP if r[1] == i]
    if not rows:
        continue
    gmv = sum(r[3] for r in rows)
    inc = sum(r[4] for r in rows)
    sub = sum(r[5] + r[6] for r in rows)
    exp = sum(r[7] for r in rows)
    vis = sum(r[8] for r in rows)
    val = sum(r[10] for r in rows)
    d0, d1 = pdate(st['first']), pdate(st['last'])
    cal = (d1 - d0).days + 1
    cris = [r for r in CPC if r[1] == i]
    cost = sum(r[3] for r in cris)
    cvis = sum(r[5] for r in cris)
    store_stat.append(dict(
        name=st['name'], brand=st['brand'], si=i, d0=d0, d1=d1,
        days=st['days'], cal=cal, gmv=gmv, inc=inc, sub=sub, exp=exp, vis=vis, val=val,
        incomeRate=inc / gmv if gmv else 0, subRate=sub / gmv if gmv else 0,
        aov=gmv / val if val else 0, visitRate=vis / exp if exp else 0,
        cost=cost, cvis=cvis, perDay=gmv / st['days'] if st['days'] else 0,
        plats=[p for p in PLATFORMS if st['ids'].get(p)],
    ))

for x in sorted(store_stat, key=lambda z: -z['days']):
    print('%-22s %-5s %5d %6d %10.0f %7.1f%% %7.1f%% %8.1f %7.2f%%' % (
        x['name'], x['brand'], x['days'], x['cal'], x['gmv'],
        x['incomeRate'] * 100, x['subRate'] * 100, x['aov'], x['visitRate'] * 100))

print()
print('存活天数分布: 中位数 %.0f 天, 均值 %.0f 天, 最短 %d 天, 最长 %d 天' % (
    statistics.median([x['days'] for x in store_stat]),
    statistics.mean([x['days'] for x in store_stat]),
    min(x['days'] for x in store_stat), max(x['days'] for x in store_stat)))
print('存活 < 90 天的门店: %d 家 (%.0f%%)' % (
    sum(1 for x in store_stat if x['days'] < 90),
    sum(1 for x in store_stat if x['days'] < 90) / len(store_stat) * 100))

# ---------------- 关店时间线 ----------------
print()
print('=' * 78)
print('【3】关店时间线 vs 疫情节点')
print('=' * 78)
closed = sorted(store_stat, key=lambda z: z['d1'])
print('%-22s %-12s %-12s %6s %10s' % ('门店', '开业', '最后有数据', '存活', '累计GMV'))
print('-' * 78)
for x in closed:
    print('%-22s %-12s %-12s %5d天 %10.0f' % (x['name'], x['d0'], x['d1'], x['days'], x['gmv']))

print()
print('--- 按"最后有数据月份"归堆 ---')
byclose = collections.Counter(x['d1'].strftime('%Y-%m') for x in closed)
for k in sorted(byclose):
    names = [x['name'] for x in closed if x['d1'].strftime('%Y-%m') == k]
    print('  %s : %d 家  %s' % (k, byclose[k], '、'.join(names)))

print()
print('--- 疫情关键节点 ---')
print('  2020-01-23 武汉封城（除夕前一天）')
print('  2020-01-24 上海启动重大突发公共卫生事件一级响应')
print('  2020-02-xx 全国餐饮堂食基本停摆，仅存外卖')
print('  2020-03-xx 上海逐步复工复产，餐饮限流')
print('  2020-06-xx 北京新发地疫情反复')
pre = sum(1 for x in closed if x['d1'] < datetime.date(2020, 1, 23))
post = len(closed) - pre
print('  疫情前(2020-01-23 之前)已停业: %d 家' % pre)
print('  疫情后停业: %d 家' % post)

# ---------------- 月度演进 ----------------
print()
print('=' * 78)
print('【4】月度演进：在营数 / GMV / 补贴率')
print('=' * 78)
months = sorted(set(DATES[r[0]][:7] for r in SHOP))
print('%-9s %5s %11s %11s %8s %8s %8s' % ('月份', '在营店', 'GMV', '商家实收', '实收率', '补贴率', '客单价'))
print('-' * 78)
prev_gmv = None
for m in months:
    rows = [r for r in SHOP if DATES[r[0]][:7] == m]
    if not rows:
        continue
    gmv = sum(r[3] for r in rows)
    inc = sum(r[4] for r in rows)
    sub = sum(r[5] + r[6] for r in rows)
    val = sum(r[10] for r in rows)
    n = len(set(r[1] for r in rows))
    tag = ''
    if prev_gmv:
        ch = (gmv - prev_gmv) / prev_gmv * 100
        tag = '  %+.1f%%' % ch
    print('%-9s %5d %11.0f %11.0f %7.1f%% %7.1f%% %8.1f%s' % (
        m, n, gmv, inc, inc / gmv * 100, sub / gmv * 100, gmv / val if val else 0, tag))
    prev_gmv = gmv

# ---------------- 单店月度表现 ----------------
print()
print('=' * 78)
print('【5】每家门店的月度 GMV 轨迹（看关店前是否衰减）')
print('=' * 78)
for x in sorted(store_stat, key=lambda z: -z['days']):
    rows = [r for r in SHOP if r[1] == x['si']]
    mm = collections.defaultdict(lambda: [0.0, 0, 0.0])  # gmv, orders, sub
    for r in rows:
        k = DATES[r[0]][:7]
        mm[k][0] += r[3]
        mm[k][1] += r[10]
        mm[k][2] += r[5] + r[6]
    ks = sorted(mm)
    parts = []
    for k in ks:
        parts.append('%s:%.0f' % (k[2:], mm[k][0]))
    first, last = mm[ks[0]][0], mm[ks[-1]][0]
    drop = (first - last) / first * 100 if first else 0
    print('%-22s [%s]  首月¥%.0f→末月¥%.0f (%+.0f%%)' % (x['name'], ' '.join(parts), first, last, -drop))

# ---------------- 平台维度 ----------------
print()
print('=' * 78)
print('【6】平台维度（品牌内）')
print('=' * 78)
for b in BRANDS:
    sis = [i for i, st in enumerate(STORES) if st['brand'] == b]
    print('【%s】' % b)
    for pi, p in enumerate(PLATFORMS):
        rows = [r for r in SHOP if r[1] in sis and r[2] == pi]
        if not rows:
            print('   %s: 无数据' % p)
            continue
        gmv = sum(r[3] for r in rows)
        inc = sum(r[4] for r in rows)
        sub = sum(r[5] + r[6] for r in rows)
        msub = sum(r[5] for r in rows)
        exp = sum(r[7] for r in rows)
        vis = sum(r[8] for r in rows)
        odr = sum(r[9] for r in rows)
        val = sum(r[10] for r in rows)
        nstore = len(set(r[1] for r in rows))
        cris = [r for r in CPC if r[1] in sis and r[2] == pi]
        cost = sum(r[3] for r in cris)
        cvis = sum(r[5] for r in cris)
        print('   %-4s | 店%d | GMV ¥%.0f (%.0f%%) | 实收率 %.1f%% | 补贴率 %.1f%%(商家%.1f%%) | 佣金率 %.2f%%' % (
            p, nstore, gmv, gmv / sum(r[3] for r in SHOP if r[1] in sis) * 100,
            inc / gmv * 100, sub / gmv * 100, msub / gmv * 100,
            (gmv - inc - sub) / gmv * 100))
        print('        | 进店率 %.2f%% | 下单率 %.2f%% | 客单价 ¥%.1f | 到店成本 %s | 付费进店占比 %s' % (
            vis / exp * 100, odr / vis * 100, gmv / val,
            '¥%.2f' % (cost / cvis) if cvis else '--',
            '%.1f%%' % (cvis / vis * 100) if vis else '--'))
    print()

# ---------------- 单店经济模型 ----------------
print('=' * 78)
print('【7】单店经济模型：单店月均产出能否支撑一家门店')
print('=' * 78)
for x in sorted(store_stat, key=lambda z: -z['days']):
    mcount = x['cal'] / 30.44
    print('%-22s 存活%3d天(≈%.1f月) | 月均GMV ¥%6.0f | 月均实收 ¥%6.0f | 日均GMV ¥%5.0f | 单均GMV ¥%.1f' % (
        x['name'], x['days'], mcount, x['gmv'] / mcount, x['inc'] / mcount,
        x['perDay'], x['gmv'] / x['val'] if x['val'] else 0))

print()
top = max(store_stat, key=lambda z: z['perDay'])
print('单店日均 GMV 最高: %s ¥%.0f/天' % (top['name'], top['perDay']))
print('全部门店日均 GMV 中位数: ¥%.0f/天' % statistics.median([x['perDay'] for x in store_stat]))
