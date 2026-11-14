import sys, tarfile, collections
bad=[]; types=collections.Counter(); tops=set(); total=0
with tarfile.open(sys.argv[1]) as t:
    for m in t:
        n=m.name; total+=m.size
        tops.add(n.split('/')[0])
        if n.startswith('/') or '..' in n.split('/') or '\\' in n: bad.append(('path',n))
        if m.issym() or m.islnk(): bad.append(('link',n,m.linkname))
        if not (m.isfile() or m.isdir()): types['other']+=1; bad.append(('type',n,m.type))
        else: types['file' if m.isfile() else 'dir']+=1
print('top-level:',tops); print(types); print('uncompressed bytes',total); print('bad',len(bad),bad[:20])
