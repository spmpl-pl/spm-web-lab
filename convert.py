import json;
import hashlib;

data=json.load(open("UserData.json"));
for k,v in data.items():
    v["username"] = v["first_name"] + v["last_name"][0];
    if "password" not in v: v["password"]=hashlib.md5(v["email"].encode()).hexdigest();
json.dump(data, open("UserData2.json","w"), indent=2)