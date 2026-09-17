# -*- coding: utf-8 -*-
"""补充分析：关店前是否衰减、扩张节奏、同区域重复布点、疫情冲击量化。"""
import json, io, os, collections, datetime

BASE = r'C:\Users\25785\WorkBuddy\2026-09-15-16-50-57'
s = io.open(os.path.join(BASE, 'dashboard-data.js'), encoding='utf-8').read()
d = json.loads(s[s.index('{'):s.rindex('}') + 1])
DATES, STORES, PLATFORMS, BRANDS = d['dates'], d['stores'], d['platforms'], d['brands']
SHOP, CPC = d['shop'], d['cpc']
pd_ = lambda x: datetime.date(*[int(v) for v in x.split('-')])

print('=' * 78)
print('【A】关店前 30 天 vs 更早 30 天：是衰败而亡，还是被主动终止？')
print('=' * 78)
for i, st in enumerate(sorted(STORES, key=lambda z: z['last'])):
    si = STORES.index(st)
    rows = sorted([r for r in SHOP if r[1] == si], key=lambda r: r[0])
    last_d = pd_(st['last'])
    w1 = [r for r in rows if (last_d - pd_(DATES[r[0]])).days < 30]
    w2 = [r for r in rows if 30 <= (last_d - pd_(DATES[r[0]])).days < 60]
    g1 = sum(r[3] for r in w1)
    g2 = sum(r[3] for r in w2)
    if g2 > 0:
        ch = (g1 - g2) / g2 * 100
        verdict = '衰减而亡' if ch < -20 else ('平稳' if abs(ch) <= 20 else '增长中被终止')
    else:
        ch, verdict = None, '数据不足'
    print('%-22s 停业%s | 末30天¥%7.0f 前30天¥%7.0f  %s  %s' % (
        st['name'], st['last'], g1, g2,
        ('%+.0f%%' % ch) if ch is not None else '   --  ', verdict))

print()
print('=' * 78)
print('【B】扩张节奏：每月新开 / 停业 / 净在营')
print('=' * 78)
opened = collections.Counter(st['first'][:7] for st in STORES)
closed = collections.Counter(st['last'][:7] for st in STORES)
allm = sorted(set(list(opened) + list(closed)))
print('%-9s %6s %6s %8s' % ('月份', '新开', '停业', '累计店数'))
cum = 0
for m in allm:
    cum += opened.get(m, 0) - closed.get(m, 0)
    print('%-9s %6d %6d %8d' % (m, opened.get(m, 0), closed.get(m, 0), cum))

print()
print('  ★ 开业高峰: 2019-11 单月开 %d 家；2019-12 开 %d 家' % (
    opened.get('2019-11', 0), opened.get('2019-12', 0)))
print('  ★ 停业高峰: 2019-12 单月停 %d 家（疫情爆发前 1 个月）' % closed.get('2019-12', 0))
print('  ★ 从 9 家峰值到 2 家，用时 %d 个月，口罩前就已关停 6 家' %
      ((datetime.date(2020, 9, 1) - datetime.date(2019, 12, 1)).days // 30))

print()
print('=' * 78)
print('【C】同区域重复布点（自我竞争）')
print('=' * 78)
DISTRICTS = {
    '龙阳路店': '浦东·龙阳路', '龙阳广场店': '浦东·龙阳路', '交大店': '徐汇·交大',
    '大宁店': '静安·大宁', '真如店': '普陀·真如', '怒江路店': '普陀·怒江路',
    '武宁路店': '普陀·武宁路', '宝山店': '宝山', '五角场店': '杨浦·五角场',
    '虹口足球场店': '虹口·足球场',
}
groups = collections.defaultdict(list)
for st in STORES:
    short = st['name'].split('-')[-1]
    groups[DISTRICTS.get(short, short)].append(st)
for area, sts in sorted(groups.items()):
    if len(sts) > 1:
        print('  【%s】%d 家: %s' % (area, len(sts),
              ' | '.join('%s(%s~%s)' % (x['name'].split('-')[-1], x['first'], x['last']) for x in sts)))
print()
print('  ★ 龙阳路 400 米内先后开 2 家（11-08 与 12-20 相隔 42 天），前一家关店 12 天后后一家开业')
print('  ★ 普陀区一个区先后布局 3 家（真如、怒江路、武宁路）')

print()
print('=' * 78)
print('【D】疫情冲击量化：2019-12（疫情前峰值） vs 2020-02（谷底）')
print('=' * 78)
peak = [r for r in SHOP if DATES[r[0]][:7] == '2019-12']
trough = [r for r in SHOP if DATES[r[0]][:7] == '2020-02']
for label, rows in [('2019-12 峰值月', peak), ('2020-02 谷底月', trough)]:
    gmv = sum(r[3] for r in rows)
    val = sum(r[10] for r in rows)
    vis = sum(r[8] for r in rows)
    exp = sum(r[7] for r in rows)
    sub = sum(r[5] + r[6] for r in rows)
    print('%-16s 门店%d家 | GMV ¥%8.0f | 有效订单 %6d | 曝光 %8d | 进店率 %.2f%% | 补贴率 %.1f%% | 客单价 ¥%.1f' % (
        label, len(set(r[1] for r in rows)), gmv, val, exp, vis / exp * 100, sub / gmv * 100, gmv / val))
g1 = sum(r[3] for r in peak); g2 = sum(r[3] for r in trough)
print('  ★ 全盘 GMV 从 ¥%.0f 跌到 ¥%.0f，%.0f%%' % (g1, g2, (g2 - g1) / g1 * 100))

# 存续门店对比：宝山店在疫情前后的表现
print()
print('  --- 唯一贯穿全周期的宝山店：疫情前后月度对比 ---')
bs = STORES.index([x for x in STORES if x['name'] == '蛙小辣-宝山店'][0])
bsm = collections.defaultdict(float)
for r in SHOP:
    if r[1] == bs:
        bsm[DATES[r[0]][:7]] += r[3]
for k in sorted(bsm):
    pre = '疫情前' if k < '2020-01' else '疫情后'
    print('     %s ¥%8.0f  %s' % (k, bsm[k], pre))

print()
print('=' * 78)
print('【E】补贴结构：到底是谁在补贴谁')
print('=' * 78)
gmv = sum(r[3] for r in SHOP)
inc = sum(r[4] for r in SHOP)
msub = sum(r[5] for r in SHOP)
psub = sum(r[6] for r in SHOP)
comm = gmv - inc - msub - psub
print('  GMV             ¥%10.0f  100.0%%' % gmv)
print('  商家实收         ¥%10.0f  %5.1f%%' % (inc, inc / gmv * 100))
print('  商家自掏补贴     ¥%10.0f  %5.1f%%   <- 占补贴总额 %.1f%%' % (
    msub, msub / gmv * 100, msub / (msub + psub) * 100))
print('  平台承担补贴     ¥%10.0f  %5.1f%%   <- 占补贴总额 %.1f%%' % (
    psub, psub / gmv * 100, psub / (msub + psub) * 100))
print('  平台抽佣         ¥%10.0f  %5.1f%%' % (comm, comm / gmv * 100))
print()
print('  ★ 商家每卖出 ¥100 的货：自己拿回 ¥%.0f，自掏 ¥%.0f 做补贴，被平台抽走 ¥%.0f' % (
    inc / gmv * 100, msub / gmv * 100, comm / gmv * 100))
print('  ★ 平台只承担了全部补贴的 %.1f%%，其余 %.1f%% 由商家自己出' % (
    psub / (msub + psub) * 100, msub / (msub + psub) * 100))

print()
print('=' * 78)
print('【F】单店能否养活自己（用实收 vs 上海餐饮固定成本粗估）')
print('=' * 78)
print('%-22s %8s %10s %10s %10s' % ('门店', '存活天', '总实收', '月均实收', '结论'))
print('-' * 78)
for st in sorted(STORES, key=lambda z: -z['days']):
    si = STORES.index(st)
    rows = [r for r in SHOP if r[1] == si]
    inc = sum(r[4] for r in rows)
    cal = (pd_(st['last']) - pd_(st['first'])).days + 1
    mavg = inc / (cal / 30.44)
    verdict = '不可能覆盖' if mavg < 30000 else ('极度紧张' if mavg < 60000 else '才有可行性')
    print('%-22s %8d %10.0f %10.0f %10s' % (st['name'], st['days'], inc, mavg, verdict))
print()
print('  参考：上海 30-60㎡ 快餐店月固定成本（租金+人工+水电）约 ¥3.0~6.0 万')
