from core.rpc_client import RemoteObjectCollection




f = RemoteObjectCollection()

print(f.keys())

s = f['s']
b = f['b']

print(s.a)
s.a = 10
print(s.a)
s.doIt()
print(s.a)
s.doItNow(23)
print(s.b)
print(s.a)
print(type(s))
print(s.g)
print(s.c)
print(b.getTest())
