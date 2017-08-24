import neapi
import urllib

file0 = open(".\\tmp.txt","w")
x = {"csrf_token":"","id":"93878593","limit":"20","n":"1000","offset":"0","total":"false"}
enc = neapi.NEEncrypt()
enc.loadParams(x)
result = urllib.urlencode(enc.getEncryptedData())
file0.write(result)
print result
file0.close()