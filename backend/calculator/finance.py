"""Pure financial calculations. All amounts are Decimal tomans."""
from decimal import Decimal, InvalidOperation, localcontext

class FinanceError(ValueError):
    pass

def number(value, label):
    try:
        if isinstance(value, bool) or value is None or isinstance(value, float):
            raise ValueError()
        result = Decimal(str(value))
        if not result.is_finite() or result.adjusted() > 24 or result.adjusted() < -18:
            raise ValueError()
        if result < 0:
            raise FinanceError(f'{label} نمی‌تواند منفی باشد.')
        return result
    except (InvalidOperation, ValueError, TypeError) as exc:
        if isinstance(exc, FinanceError):
            raise
        raise FinanceError(f'{label} باید یک عدد معتبر باشد.')

def rate(value, label='نرخ اعتبار'):
    r = number(value, label)
    if r >= 100:
        raise FinanceError(f'{label} باید از صفر تا کمتر از ۱۰۰ درصد باشد.')
    return r / 100

def credit_for(base, r, mode, value, inverse=False):
    maximum = base * r if inverse else base * r / (1-r)
    if mode == 'max':
        used = maximum
    elif mode == 'percent':
        p = number(value, 'درصد اعتبار مصرفی')
        if p > 100:
            raise FinanceError('درصد اعتبار مصرفی باید بین صفر و ۱۰۰ باشد.')
        used = maximum * p / 100
    elif mode == 'amount':
        used = number(value, 'اعتبار مصرفی')
        if used > maximum:
            raise FinanceError('اعتبار مصرفی از سقف مجاز این سناریو بیشتر است.')
    else:
        raise FinanceError('روش استفاده از اعتبار معتبر نیست.')
    return used, maximum

def calculate(data):
    with localcontext() as ctx:
        ctx.prec = 50
        kind = data.get('scenario')
        r = rate(data.get('rate'))
        mode = data.get('credit_mode')
        value = data.get('credit_value')
        if kind == 'direct':
            capital = number(data.get('capital'), 'سرمایه اولیه')
            used, maximum = credit_for(capital, r, mode, value)
            total = capital + used
            return dict(capital=capital, used_credit=used, max_credit=maximum, asset_value=total, collateral=total*r)
        if kind == 'reverse':
            total = number(data.get('target'), 'ارزش هدف')
            used, maximum = credit_for(total, r, mode, value, True)
            return dict(capital=total-used, used_credit=used, max_credit=maximum, asset_value=total, collateral=total*r)
        if kind in ('convert_direct', 'convert_reverse'):
            source_r = rate(data.get('source_rate'), 'نرخ اعتبار مبدأ')
            source = number(data.get('source_value'), 'ارزش کل دارایی مبدأ')
            debt = number(data.get('source_debt'), 'اعتبار فعلی مبدأ')
            if debt > source * source_r:
                raise FinanceError('اعتبار فعلی از ارزش تضمینی دارایی مبدأ بیشتر است.')
            if kind == 'convert_direct':
                settled = debt
                sold = source
                capital = sold - settled
                used, maximum = credit_for(capital, r, mode, value)
                total = capital + used
            else:
                total = number(data.get('target'), 'ارزش هدف مقصد')
                used, maximum = credit_for(total, r, mode, value, True)
                capital = total - used
                settled = number(data.get('settled'), 'اعتبار تسویه‌شده')
                if settled > debt:
                    raise FinanceError('اعتبار تسویه‌شده نمی‌تواند بیشتر از اعتبار فعلی باشد.')
                sold = capital + settled
                if sold > source:
                    raise FinanceError('دارایی مبدأ برای این فروش کافی نیست.')
            remaining_debt = debt - settled
            remaining_asset = source - sold
            if remaining_debt > remaining_asset * source_r:
                raise FinanceError('اعتبار باقی‌مانده از ارزش تضمینی دارایی باقی‌مانده بیشتر است؛ مبلغ تسویه را افزایش دهید یا هدف را تغییر دهید.')
            return dict(sold=sold, settled=settled, remaining_debt=remaining_debt, remaining_asset=remaining_asset, capital=capital, used_credit=used, max_credit=maximum, asset_value=total, collateral=total*r)
        raise FinanceError('نوع محاسبه معتبر نیست.')
