from pathlib import Path
import sqlite3
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'construction_control.db'
EXPECTED={
'Jamie Murray':('Electrician','AWS Badge','#ff0000'),"Lorcan O'Toole":('Electrician','AWS Badge','#ff0000'),'Sean Timlin':('2nd Year','AWS Badge','#00ff00'),'Calum Daly':('2nd Year','Airport Badge + AWS Badge','#00ff00'),'Ian Fox (T)':('Site Management','AWS Badge','#ffbd0a'),'Jordan Lawrence':('Site Management','AWS Badge','#ffbd0a'),'Jake Sherlock':('Site Management','AWS Badge','#ffbd0a'),'Mark Gibson (T)':('Charge Hand','AWS Badge','#5b8f3b'),'Conor Fitzpatrick (T)':('Charge Hand','AWS Badge','#5b8f3b'),'Pratik Kamble':('Engineers','','#f6d1ab'),'Ross Douglas':('Engineers','Airport Badge','#f6d1ab'),'Dean Smith':('Electrician','AWS Badge','#ff0000'),'Keith Murray':('Electrician','AWS Badge','#ff0000'),'Conor Snell':('Electrician','Airport Badge + AWS Badge','#ff0000'),'Colm Cox':('Electrician','Airport Badge + AWS Badge','#ff0000'),'Vijay Sundaram (T)':('Electrician','AWS Badge','#ff0000'),'Christian Williams':('Electrician','Airport Badge + AWS Badge','#ff0000'),'Adam Poole':('Electrician','Airport Badge + AWS Badge','#ff0000'),'Dean Flynn':('4th Year','AWS Badge','#ff00d8'),"Luke O'Reilly":('3rd Year','AWS Badge','#ffff00'),'Darragh Murray':('2nd Year','AWS Badge','#00ff00'),'Lee Gallagher':('2nd Year','AWS Badge','#00ff00'),'Sean Boyle':('2nd Year','Airport Badge + AWS Badge','#00ff00'),'Darius Dragusin':('2nd Year','AWS Badge','#00ff00'),'Stephen Blake':('GO','AWS Badge','#c0c0c0'),'Anthony Murphy':('Site Management','AWS Badge','#ffbd0a'),'John Shelley (T)':('Charge Hand','AWS Badge','#5b8f3b'),'Keith Murphy':('Site Management','AWS Badge','#ffbd0a'),'William O Brien':('Site Management','AWS Badge','#ffbd0a'),'Colm Keighery':('Unspecified','','#ffffff')}
def test_image_staff_register():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    rows=con.execute("SELECT name,labour_level,badge_type,display_color,active FROM staff WHERE company_id='C1' AND active=1").fetchall()
    got={r['name']:(r['labour_level'],r['badge_type'],r['display_color']) for r in rows}
    assert len(got)==30
    for name,expected in EXPECTED.items(): assert got.get(name)==expected
    con.close()
