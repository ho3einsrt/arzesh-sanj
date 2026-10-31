import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

type Asset = 'gold'|'stock'|'fixed';
@Component({selector:'app-root', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./app.component.html'})
export class AppComponent {
  constructor(private http: HttpClient) {}
  scenario = 'direct'; asset: Asset = 'gold'; source: Asset = 'fixed';
  rates: Record<Asset,string> = {gold:'44', stock:'55', fixed:'60.5'};
  names: Record<Asset,string> = {gold:'طلا', stock:'سهام', fixed:'درآمد ثابت'};
  assets: Asset[] = ['gold','stock','fixed'];
  capital='100'; target='100'; sourceValue='100'; sourceDebt='0'; settled='0'; creditValue='50';
  unit='million'; creditMode='max'; result: Record<string,string>|null=null; error=''; loading=false;
  tabs=[{id:'direct',title:'محاسبه مستقیم',sub:'سرمایه به دارایی'},{id:'reverse',title:'محاسبه معکوس',sub:'دارایی به سرمایه'},{id:'convert_direct',title:'تبدیل دارایی',sub:'محاسبه مقصد'},{id:'convert_reverse',title:'تبدیل معکوس',sub:'محاسبه فروش'}];
  get conversion(){return this.scenario.startsWith('convert');}
  get reverse(){return this.scenario.endsWith('reverse');}
  normalize(s:string):string {return String(s ?? '').replace(/[۰-۹]/g,c=>String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c))).replace(/[٠-٩]/g,c=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(c))).replace(/[٬,\s]/g,'').replace(/٫/g,'.');}
  amount(s:string):string {const n=this.normalize(s); if(this.unit==='toman') return n; if(!/^\d+(\.\d+)?$/.test(n)) return n; const [whole, frac='']=n.split('.'); const digits=(frac+'000000'); return (whole+digits.slice(0,6)).replace(/^0+(?=\d)/,'')+(digits.slice(6) ? '.'+digits.slice(6) : '');}
  display(v:string|undefined):string {if(v===undefined) return '—'; const n=Number(v); return Number.isFinite(n) ? new Intl.NumberFormat('fa-IR',{maximumFractionDigits:2}).format(n) : v;}
  selectTab(s:string){this.scenario=s; this.result=null; this.error='';}
  submit(){
    this.loading=true; this.error=''; this.result=null;
    const payload:Record<string,string>={scenario:this.scenario,rate:this.normalize(this.rates[this.asset]),credit_mode:this.creditMode,credit_value:this.creditMode==='amount'?this.amount(this.creditValue):this.normalize(this.creditValue)};
    if(this.scenario==='direct') payload['capital']=this.amount(this.capital);
    if(this.reverse) payload['target']=this.amount(this.target);
    if(this.conversion){payload['source_rate']=this.normalize(this.rates[this.source]);payload['source_value']=this.amount(this.sourceValue);payload['source_debt']=this.amount(this.sourceDebt);if(this.reverse)payload['settled']=this.amount(this.settled);}
    this.http.post<Record<string,string>>('/api/calculate/', payload).subscribe({
      next: data => { this.result=data; this.loading=false; },
      error: (err: HttpErrorResponse) => {
        this.error = typeof err.error?.error === 'string' ? err.error.error : 'ارتباط با سرور برقرار نشد. از اجرای بک‌اند اطمینان حاصل کنید.';
        this.loading=false;
      }
    });
  }
}
