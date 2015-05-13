""" Register node at server. Run before uploading data. Usage in README"""

import json
import upload

with open("config/node.json") as nodeConfigFile:
    nodeCfgs = json.load(nodeConfigFile)

nodeName = nodeCfgs["node"]["name"]
if nodeName == "default":
    print """Please update node name in node.json file. For more information,
    check README."""
else:
    data = [{"name": nodeName}]
    data.append("register")
    ack = upload.upload(json.dumps(data) + "\r\n\r\n")
    print ack
    if ack.startswith("SUCCESS"):
        node_id = (int) (ack.split()[-1])
        with open("config/node.json", "w") as nodeCfgFilew:
            nodeCfgs["node"]["node_id"] = node_id
            json.dump(nodeCfgs, nodeCfgFilew)
            
        
