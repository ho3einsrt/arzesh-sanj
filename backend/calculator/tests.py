import json
from decimal import Decimal
from django.test import SimpleTestCase, Client
from .finance import calculate, FinanceError

class FinancialTests(SimpleTestCase):
    def run_calc(self, **kw):
        return calculate(kw)
    def test_acceptance_direct_and_reverse(self):
        direct = self.run_calc(scenario='direct', capital='100000000', rate='44', credit_mode='max')
        self.assertAlmostEqual(direct['asset_value'], Decimal('178571428.5714285714285714286'), places=18)
        self.assertAlmostEqual(direct['used_credit'], Decimal('78571428.57142857142857142857'), places=18)
        self.assertAlmostEqual(direct['collateral'], direct['used_credit'], places=18)
        reverse = self.run_calc(scenario='reverse', target=str(direct['asset_value']), rate='44', credit_mode='max')
        self.assertAlmostEqual(reverse['capital'], Decimal('100000000'), places=18)
    def test_direct_percent_and_amount(self):
        p = self.run_calc(scenario='direct', capital='100000000', rate='44', credit_mode='percent', credit_value='50')
        self.assertAlmostEqual(p['used_credit'], Decimal('39285714.28571428571428571429'), places=18)
        a = self.run_calc(scenario='direct', capital='100', rate='50', credit_mode='amount', credit_value='50')
        self.assertEqual(a['asset_value'], 150)
    def test_reverse_percent_and_amount(self):
        p = self.run_calc(scenario='reverse', target='100', rate='50', credit_mode='percent', credit_value='50')
        self.assertEqual(p['used_credit'], 25)
        self.assertEqual(p['capital'], 75)
        a = self.run_calc(scenario='reverse', target='100', rate='50', credit_mode='amount', credit_value='50')
        self.assertEqual(a['capital'], 50)
    def test_conversion_full(self):
        r = self.run_calc(scenario='convert_direct', source_value='100', source_debt='40', source_rate='44', rate='55', credit_mode='max')
        self.assertEqual(r['capital'], 60)
        self.assertEqual(r['settled'], 40)
        self.assertEqual(r['remaining_debt'], 0)
        self.assertAlmostEqual(r['asset_value'], Decimal('133.3333333333333333333333333'), places=18)
    def test_conversion_partial(self):
        r = self.run_calc(scenario='convert_reverse', source_value='200', source_debt='50', source_rate='60.5', target='100', rate='44', credit_mode='max', settled='20')
        self.assertEqual(r['sold'], 76)
        self.assertEqual(r['capital'], 56)
        self.assertEqual(r['remaining_debt'], 30)
        self.assertEqual(r['remaining_asset'], 124)
    def test_invalid_and_boundaries(self):
        base = dict(scenario='direct', capital='100', rate='44', credit_mode='amount', credit_value='0')
        for changes in [dict(capital='-1'),dict(rate='100'),dict(rate='-1'),dict(rate='NaN'),dict(credit_value='79'),dict(credit_mode='percent',credit_value='101'),dict(capital=''),dict(capital='Infinity')]:
            with self.subTest(changes=changes), self.assertRaises(FinanceError): self.run_calc(**(base | changes))
        self.assertEqual(self.run_calc(**(base | dict(rate='0')))['asset_value'], 100)
        self.assertEqual(self.run_calc(**(base | dict(capital='0',credit_mode='max')))['asset_value'], 0)
        self.assertEqual(self.run_calc(**(base | dict(rate='50',credit_value='100')))['asset_value'], 200)
    def test_invalid_conversion(self):
        base=dict(scenario='convert_reverse',source_value='100',source_debt='40',source_rate='50',target='80',rate='50',credit_mode='max',settled='0')
        for changes in [dict(source_debt='51'),dict(settled='41'),dict(target='300'),dict(target='150',settled='0')]:
            with self.subTest(changes=changes), self.assertRaises(FinanceError): self.run_calc(**(base | changes))
    def test_api(self):
        c=Client()
        response=c.post('/api/calculate/',data=json.dumps(dict(scenario='direct',capital='100',rate='44',credit_mode='max')),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertIsInstance(response.json()['asset_value'],str)
        self.assertEqual(c.post('/api/calculate/',data='{}',content_type='application/json').status_code,400)
        self.assertEqual(c.get('/api/calculate/').status_code,405)
