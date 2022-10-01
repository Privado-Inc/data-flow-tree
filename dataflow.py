import json
import re
import sys

if len(sys.argv) < 2:
    print("Pass the privado json path")
    exit(1)

privadoJson = sys.argv[1]
print("privado json passed is : " + privadoJson)


def extractDomainFromUrlVerifyIPAddress(url):
    # Extract Domain name from url & set it as vendorName
    urlSplit = re.split('\.|://', url)
    domain = ''
    extension = re.split('\/', urlSplit[-1])

    isIPAddress = re.match('.{0,20}\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) != None
    if isIPAddress:
        return True, '.'.join([urlSplit[-4], urlSplit[-3], urlSplit[-2], extension[0]])
    
    # Specific condition to handle google.gov.in or google.org.us kind of case
    res = re.findall("[.](?:com|net|co|gov|edu|org|info|web|mil)[.]", url)

    # Try to get sub-domain/service if available
    if len(urlSplit) > 3:
        if urlSplit[-3] == 'www':
            domain = urlSplit[-2] + '.' + extension[0]
        else:
            if len(res):
                domain = '.'.join([urlSplit[-3], urlSplit[-2], extension[0]])
            else:
                domain = '.'.join([urlSplit[-2], extension[0]])
    else:
        if len(res):
            domain = '.'.join([urlSplit[-3], urlSplit[-2], extension[0]])
        else:
            domain = '.'.join([urlSplit[-2], extension[0]])

    return False, domain.strip('"`\'').lower()



with open(privadoJson) as file:
    privadoJsonData = json.loads(file.read())

    ruleIdNameMap = dict()
    for sourceItem in privadoJsonData["sources"]:
        ruleIdNameMap[sourceItem["id"]] = sourceItem["name"]

    processingMap = dict()
    for processingItem in privadoJsonData["processing"]:
        processingMap[processingItem["sourceId"]] = len(processingItem["occurrences"])

    #sharing thirdParty
    sharingMap = dict()
    for thirdParty in privadoJsonData["dataFlow"]["third_parties"]:
        sharingMap[thirdParty["sourceId"]] = set()
        for sink in thirdParty["sinks"]:
            if not sink["apiUrl"]:
                sharingMap[thirdParty["sourceId"]].add(sink["name"])
            else:
                for api in sink.get("apiUrl", ""):
                    domainres, domain = extractDomainFromUrlVerifyIPAddress(api)
                    if domainres:
                        sharingMap[thirdParty["sourceId"]].add(domain)
    #sharing internalAPI
    for internalApi in privadoJsonData["dataFlow"]["internal_apis"]:
        if internalApi["sourceId"] not in sharingMap:
            sharingMap[internalApi["sourceId"]] = set()
        for sink in internalApi["sinks"]:
            for api in sink.get("apiUrl", ""):
                domainres, domain = extractDomainFromUrlVerifyIPAddress(api)
                if domainres:
                    sharingMap[internalApi["sourceId"]].add(domain)


    #storage
    storageMap = dict()
    for storage in privadoJsonData["dataFlow"]["storages"]:
        storageMap[storage["sourceId"]] = []
        for sink in storage["sinks"]:
            storageMap[storage["sourceId"]].append(sink["name"])



    #leakages
    leakageMap = dict()
    for leakage in privadoJsonData["dataFlow"]["leakages"]:
        leakageMap[leakage["sourceId"]] = []
        for sink in leakage["sinks"]:
            leakageMap[leakage["sourceId"]].append({"name" : sink["name"], "count" : len(sink["paths"])})


    #collection 
    collectionMap = dict()
    for frameworkCollection in privadoJsonData["collections"]:
        for collection in frameworkCollection["collections"]:
            if collection["sourceId"] not in collectionMap:
                collectionMap[collection["sourceId"]] = []
            for occ in collection["occurrences"]:
                collectionMap[collection["sourceId"]].append(occ["endPoint"])

   
    privadoDataflowData = []
    for sourceItem in privadoJsonData["sources"]:
        dataElementObj = dict()
        dataElementObj["name"] = ruleIdNameMap[sourceItem["id"]]
        dataElementChildren = []

        #sharing
        sharingChildren = []
        for sharing in sharingMap.get(sourceItem["id"], ""):
            sharingChildren.append({"name" : sharing})
        if sharingChildren:
            dataElementChildren.append({"name" : "Sharing", "children" : sharingChildren})

        #storage
        storageChildren = []
        for storage in storageMap.get(sourceItem["id"], ""):
            storageChildren.append({"name" : storage})
        if storageChildren:
            dataElementChildren.append({"name" : "Storages" , "children" : storageChildren})

        #leakage
        leakageChildren = []
        for leakageType in leakageMap.get(sourceItem["id"], ""):
            if leakageType:
                leakageChildren.append({"name" : str(leakageType["count"]) + " " + leakageType["name"]})
        
        if leakageChildren:
            dataElementChildren.append({"name" : "Leakages", "children" : leakageChildren})

        #collection
        collectionChildren = []
        for endPoint in collectionMap.get(sourceItem["id"], ""):
            collectionChildren.append({"name" : endPoint})
        if collectionChildren:
            dataElementChildren.append({"name" : "Collections", "children" : collectionChildren})
        
        #processing
        dataElementChildren.append({"name" : "Processing", "children" : [{"name" : str(processingMap[sourceItem["id"]]) + " Instances"}]})
        dataElementObj["children"] = dataElementChildren
        privadoDataflowData.append(dataElementObj)
    
    #finalPrivadoDataflowData = []
    #finalPrivadoDataflowData.append({"name" : "Data Elements", "parent": "null", "children": privadoDataflowData})
    with open("privadoDataflow.json", "w") as outFile:
        outFile.write(json.dumps(privadoDataflowData))
    
    import subprocess
    subprocess.run(["python3", "-m", "http.server", "8888"])
    





