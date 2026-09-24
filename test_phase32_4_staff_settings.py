import json, os, urllib.request, urllib.parse

BASE=os.getenv('TEST_BASE_URL','http://127.0.0.1:3013')
COOKIE={}

def req(path, method='GET', body=None):
    headers={'Content-Type':'application/json'}
    if COOKIE.get('cc_session'): headers['Cookie']='cc_session='+COOKIE['cc_session']
    r=urllib.request.Request(BASE+path, method=method, headers=headers)
    if body is not None: r.data=json.dumps(body).encode()
    with urllib.request.urlopen(r, timeout=5) as x:
        sc=x.headers.get('Set-Cookie','')
        if 'cc_session=' in sc: COOKIE['cc_session']=sc.split('cc_session=',1)[1].split(';',1)[0]
        return x.status, json.loads(x.read() or b'{}')

def test_staff_assignment_settings_flow():
    assert req('/api/login','POST',{'email':'owner@demo.local','password':'DemoPass!123'})[0]==200
    roles=req('/api/roles')[1]['roles']
    assert len(roles)>=9
    assert {x['name'] for x in roles} >= {'Viewer','Site User','Foreman / Charge Hand','Site Manager','Project Manager','Construction Manager','Business Unit Lead','Company Director','Company Administrator'}
    staff=req('/api/staff?active=all')[1]['staff']
    assert len(staff)>=18
    projects=req('/api/projects')[1]['projects']
    assert {'DUB10','DUB50'} <= {x['id'] for x in projects}
    # create/edit staff
    assert req('/api/staff','POST',{'staff_ref':'T32-4','name':'Phase 32.4 Test','position':'Electrician'})[0]==201
    s=[x for x in req('/api/staff?active=all')[1]['staff'] if x['staff_ref']=='T32-4'][0]
    assert req('/api/staff/'+s['id'],'PUT',{'staff_ref':'T32-4','name':'Phase 32.4 Edited','position':'Foreman','active':True})[0]==200
    # create/edit assignment
    a=req('/api/project-assignments','POST',{'staff_id':s['id'],'project_id':'DUB10','assignment_role':'Foreman','start_date':'2026-09-20','finish_date':'2026-09-30','notes':'test'})
    assert a[0]==201
    aid=a[1]['id']
    got=req('/api/project-assignments?assignment_id='+urllib.parse.quote(aid))[1]['assignments'][0]
    assert got['project_id']=='DUB10'
    assert req('/api/project-assignments/'+aid,'PUT',{'assignment_role':'Charge Hand','start_date':'2026-09-21','finish_date':'2026-10-01','assignment_status':'Held','notes':'edited'})[0]==200
    got=req('/api/project-assignments?assignment_id='+urllib.parse.quote(aid))[1]['assignments'][0]
    assert got['assignment_role']=='Charge Hand' and got['assignment_status']=='Held'
    # persistent settings
    st=req('/api/settings')[1]['settings']
    assert 'accent_color' in st
    assert req('/api/settings','PUT',{'accent_color':'#123456','sidebar_color':'#111111','background_color':'#eeeeee','card_color':'#ffffff','text_color':'#000000','density':'compact','dashboard_default':'daily'})[0]==200
    st2=req('/api/settings')[1]['settings']
    assert st2['accent_color']=='#123456' and st2['density']=='compact' and st2['dashboard_default']=='daily'
