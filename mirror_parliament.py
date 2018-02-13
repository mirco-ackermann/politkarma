import sqlite3, collections, json, os, requests, datetime, time, random, hashlib
from xml.etree import ElementTree as ET
from inflection import underscore as us

conn = sqlite3.connect('test.sqlite3')

schema = "apps/curia_vista/docs/schemas/global.xml"

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'}

# we need to bribe the server with the right cookies, otherwise it refuses to cooporate. 
cookies = requests.get('https://www.parlament.ch/de/ratsbetrieb/abstimmungen/abstimmungs-datenbank-nr', headers=headers).cookies

headers['Accept'] = 'application/atomsvc+xml;q=0.8, application/json;odata=fullmetadata;q=0.7, application/json;q=0.5, */*;q=0.1'

def delay():
    # random delay to not kill the server and to stay under the radar.
    time.sleep(random.random()*2+1)

def fetch(url):
  
  fn = "cache/"+hashlib.sha256(url.encode('utf-8')).hexdigest()
  #print(fn)

  if not os.path.isfile(fn):
    #print("not in cache")
    text = requests.get(url, headers=headers, cookies=cookies).text
    open(fn, "w").write(text)
    delay()
  else:
    #print("hit the cache")
    text = open(fn).read()
  return text

def parse_date(datestring):
    """
    parses the uggly '/Date(23944938)/' asp-net json dates into something civilized
    based on from https://stackoverflow.com/questions/18039625/converting-asp-net-json-date-into-python-datetime
    """
    EPOCH = datetime.datetime.utcfromtimestamp(0)
    if datestring is None: return None
    timepart = datestring.split('(')[1].split(')')[0]
    milliseconds = int(timepart)
    dt = datetime.datetime.fromtimestamp(milliseconds*1e-3)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

## assume only truly date fields start with /Date.
def fixup(data):
    if type(data) is str and data.startswith("/Date("):
        return parse_date(data)
    else:
        return data

def create_tables(conn, schema, skip_filter=None):
  if skip_filter is None: 
    skip_filter = lambda tablename, columnname: False
  et = ET.parse(schema)

  ns = "{http://schemas.microsoft.com/ado/2009/11/edm}"

  def convert_type(t):
    if "Int" in t: return "INTEGER"
    return "VARCHAR"

  tables = {}

  for e in et.iter(ns+'EntityType'):
    table_name = e.attrib["Name"]
    tables[table_name] = od = collections.OrderedDict()

    for ep in e.iter(ns+'Property'):
      property_name = ep.attrib['Name']
      property_type = ep.attrib['Type']
      nullable = ep.attrib.get('Nullable', 'false') == 'true'

      if skip_filter(table_name, property_name): continue
  
      od[property_name] = us(property_name) + " " + convert_type(property_type)
      length = ep.attrib.get('MaxLength', None)
      if length is not None and length != "Max":
        od[property_name] += "(%s)"%length
  
      if not nullable:
        pass
        # Don't put that in, some of their fields are not correct.
        #od[property_name] += " NOT NULL"
  
  depends_on = collections.defaultdict(list)
  for e in et.iter(ns+'Association'):
    print(e)
    rf = e.find(ns+'ReferentialConstraint')
    dest = rf.find(ns+'Principal')
    dest_tablename = dest.attrib['Role']
    source = rf.find(ns+'Dependent')
    source_tablename = source.attrib['Role']
    for d, s in zip(dest.findall(ns+'PropertyRef'), source.findall(ns+'PropertyRef')):
      d_column = d.attrib['Name']
      s_column = s.attrib['Name']
      try:
        tables[source_tablename][s_column] += " REFERENCES %s(%s)"%(us(dest_tablename), us(d_column))
        depends_on[source_tablename].append(dest_tablename)
      except KeyError:
        print("could not create foreign key from %s to %s"%(dest_tablename, source_tablename))
  
  def create_sql(k):
    v = tables[k]
    return "CREATE TABLE IF NOT EXISTS "+ us(k)+"(\n  "+",\n  ".join(v.values())+"\n);\n"

  # we need to execute the "CREATE TABLE ..." in a way that the foreign key constraints work.
  inserted = collections.OrderedDict()
  def insert(name):
    if name in inserted: return
    for n in depends_on[name]:
      insert(n)
    command = create_sql(name)
    print(command)
  
    if name in inserted: return
    conn.execute(command)
    conn.commit()
    inserted[name] = None
  for n in tables:
    insert(n)
  return list(inserted.keys()),tables

def insert_rows(js, table, column_names):
  command = 'INSERT OR REPLACE INTO %s VALUES (%s)'%(us(table), ', '.join(['?']*len(column_names)))
  print(command)
  print(column_names)
  print()

  for data in js:
    columns = [fixup(data[cn]) for cn in column_names]
    conn.execute(command, columns)
def scrape(table, url, column_names):
  select = '&$select=' + ','.join(column_names)
  #url += select

  print(url)

  parsed = json.loads(fetch(url))

  js = parsed['d']
  if type(js) == dict: # they don't seem to know if they want to do odata v1 or v2
    js = js["results"]
  #try:
  insert_rows(js, table, column_names)
  #except KeyError as e:
  if 0:
    print()
    print(json.dumps(parsed, indent=4, sort_keys=True))
    print()
    print(e)
    print(url)



table_names, tables = create_tables(conn, schema, lambda t,c: (t == "Voting" and c not in ("ID", "PersonNumber", "IdVote")))
print(table_names)
for tn in table_names[:1]:
  if tn == "Voting": continue
  url = "https://ws.parlament.ch/odata.svc/%s?"%tn
  scrape(tn, url, list(tables[tn].keys()))
conn.commit()

needed_votes = [r[0] for r in conn.execute('SELECT DISTINCT id from vote order by id')]
needed_votes.sort()
print(needed_votes)
N = 100
for start in range(0, needed_votes[-1], N):
  tn = 'Voting'
  end = start + N
  url = '''https://ws.parlament.ch/odata.svc/Voting?$filter=(Language eq 'DE') and ((IdVote ge %i) and (IdVote le %i))&$select=ID,IdVote,PersonNumber'''%(start, end)
  print(url)
  scrape(tn, url, tables[tn].keys())
