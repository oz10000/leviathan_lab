import numpy as np
from config.settings import EXIT_PARAMS  # to be set

class HybridExit:
    DEFAULT_TP_ATR = 2.5
    DEFAULT_SL_ATR = 0.7
    DEFAULT_BE_ATR = 0.6
    DEFAULT_TRAIL_ATR = 1.3
    DEFAULT_TIME_DECAY_MIN = 180
    DEFAULT_VOL_CONTRACTION_RATIO = 0.7

    def __init__(self, **kwargs):
        self.tp_atr = kwargs.get('tp_atr', self.DEFAULT_TP_ATR)
        self.sl_atr = kwargs.get('sl_atr', self.DEFAULT_SL_ATR)
        self.be_atr = kwargs.get('be_atr', self.DEFAULT_BE_ATR)
        self.trail_atr = kwargs.get('trail_atr', self.DEFAULT_TRAIL_ATR)
        self.time_decay_min = kwargs.get('time_decay_min', self.DEFAULT_TIME_DECAY_MIN)
        self.vol_contraction_ratio = kwargs.get('vol_contraction_ratio', self.DEFAULT_VOL_CONTRACTION_RATIO)

    def should_exit(self, pos, price, now, atr_hist):
        d = pos['dir']; entry = pos['entry']; atr = pos['atr']
        tp = entry + d * self.tp_atr * atr
        sl = pos.get('sl', entry - d * self.sl_atr * atr)
        trail_sl = pos.get('trail_sl', sl)
        be = pos.get('be', False); trail = pos.get('trail', False)

        if not be:
            be_th = entry + d * self.be_atr * atr
            if (d == 1 and price >= be_th) or (d == -1 and price <= be_th):
                be = True
                cost = entry * 0.001
                sl = entry + d * cost
                trail_sl = sl
        if be and not trail:
            act = entry + d * 0.8 * atr
            if (d == 1 and price >= act) or (d == -1 and price <= act):
                trail = True
        if trail:
            new_trail = price - d * self.trail_atr * atr
            if (d == 1 and new_trail > trail_sl) or (d == -1 and new_trail < trail_sl):
                trail_sl = new_trail

        dur = (now - pos['entry_time']) / 60.0
        unreal = (price - entry) / entry * d * pos['leverage']
        if dur > self.time_decay_min and unreal < 0.002 * pos['leverage']:
            return True, "time_decay", price, {}
        if atr_hist and len(atr_hist) > 10:
            cur_atr_range = max(atr_hist[-10:]) - min(atr_hist[-10:])
            if cur_atr_range / price < self.vol_contraction_ratio * pos['atr_pct_entry']:
                return True, "vol_contraction", price, {}
        if (d == 1 and price >= tp) or (d == -1 and price <= tp):
            return True, "tp", tp, {}
        if (d == 1 and price <= trail_sl) or (d == -1 and price >= trail_sl):
            return True, "trailing_sl", trail_sl, {}

        pos['be'] = be; pos['trail'] = trail
        pos['trail_sl'] = trail_sl; pos['sl'] = sl
        return False, None, None, pos
