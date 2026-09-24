import json, shutil, tempfile, threading, urllib.request, urllib.error, uuid, requests
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

ROOT=Path(__file__).resolve().parents[1]

def req(base, method, path, body=None, cookie=None, raw=None, content_type=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    headers={}
    if body is not None: headers['Content-Type']='application/json'
    if content_type: headers['Content-Type']=content_type
    if cookie: headers['Cookie']=cookie
    r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=10) as x:
            return x.status,x.read(),x.headers
    except urllib.error.HTTPError as e:
        return e.code,e.read(),e.headers

def test_execute_all_programme_buttons_and_row_actions():
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'construction_control.db'; shutil.copy(ROOT/'render_seed.db',db)
        old=app.DB_PATH; app.DB_PATH=db; app.init_db()
        srv=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
        base=f'http://127.0.0.1:{srv.server_address[1]}'
        try:
            code,_,h=req(base,'POST','/api/login',{'email':'owner@demo.local','password':'DemoPass!123'}); assert code==200
            cookie=h.get('Set-Cookie').split(';',1)[0]
            code,raw,_=req(base,'GET','/api/plans?project_id=DUB84',cookie=cookie); assert code==200
            plan=[x for x in json.loads(raw)['plans'] if x['id']=='PLAN-DUB84'][0]; pid=plan['id']
            code,raw,_=req(base,'GET',f'/api/plans/{pid}',cookie=cookie); assert code==200
            tasks=json.loads(raw)['tasks']; assert tasks
            # + Activity
            body={'name':'BUTTON TEST ACTIVITY','start_date':'2026-09-22','finish_date':'2026-09-23','percent_complete':0,'planned_men':1,'predecessor_id':None,'dependency_type':'FS','lag_days':0,'actual_start':None,'actual_finish':None,'status':'Starting','milestone':False}
            code,raw,_=req(base,'POST',f'/api/plans/{pid}/tasks',body,cookie); assert code==201; tid=json.loads(raw)['id']
            # Edit
            body['name']='BUTTON TEST ACTIVITY EDITED'; body['percent_complete']=25; body['status']='Ongoing'; body['notes']='Button execution test'
            code,_,_=req(base,'PUT',f'/api/plans/{pid}/tasks/{tid}',body,cookie); assert code==200
            # Move
            body['start_date']='2026-09-23'; body['finish_date']='2026-09-24'
            code,_,_=req(base,'PUT',f'/api/plans/{pid}/tasks/{tid}',body,cookie); assert code==200
            # Set baseline
            code,_,_=req(base,'POST',f'/api/plans/{pid}/baseline',{},cookie); assert code==200
            # Resources / Look-ahead / Baseline vs Current / Live Progress
            for endpoint in ('resources','lookahead?days=14','comparison','integration','control'):
                code,raw,_=req(base,'GET',f'/api/plans/{pid}/{endpoint}',cookie=cookie); assert code==200, (endpoint,raw[:300])
            # Update Programme: update the temporary activity.
            code,raw,_=req(base,'POST',f'/api/plans/{pid}/update',{'update_date':'2026-09-22','note':'Button test update','tasks':[{'id':tid,'percent_complete':50}]},cookie); assert code==200
            # Calendar: add and delete an exception.
            code,raw,_=req(base,'POST','/api/plan-calendar',{'project_id':'DUB84','plan_id':pid,'exception_date':'2026-12-01','working':0,'reason':'Button test'},cookie); assert code==200
            code,raw,_=req(base,'GET',f'/api/plan-calendar?project_id=DUB84&plan_id={pid}',cookie=cookie); assert code==200
            ex=[x for x in json.loads(raw)['exceptions'] if x['exception_date']=='2026-12-01'][0]
            code,_,_=req(base,'DELETE',f'/api/plan-calendar/{ex["id"]}',cookie=cookie); assert code==200
            # Export Excel, then feed that exported workbook back through Import Excel validation.
            code,exported,h=req(base,'GET',f'/api/plan-export/{pid}',cookie=cookie); assert code==200 and len(exported)>1000 and 'spreadsheetml' in h.get('Content-Type','')
            rr=requests.post(base+f'/api/plan-import/roundtrip?plan_id={pid}&commit=0',files={'file':('DUB84_roundtrip.xlsx',exported,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},cookies={cookie.split('=',1)[0]:cookie.split('=',1)[1]},timeout=10)
            assert rr.status_code==200, rr.text
            assert rr.json()['rows_processed']>0
            # Delete temporary activity.
            code,_,_=req(base,'DELETE',f'/api/plans/{pid}/tasks/{tid}',cookie=cookie); assert code==200
        finally:
            srv.shutdown(); srv.server_close(); th.join(timeout=2); app.DB_PATH=old
