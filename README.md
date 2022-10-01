# data-flow-tree

Generate data flow tree by passing privado.json (output of privado code scanning utility)

## Prerequisite 

1. Python3 installed on your machine.
2. port 8888 must be free

## Steps to run this utility.

1. Clone this repository.
2. Run command `python3 dataflow.py <repo folder location>/.privado/privado.json` 

Above command should run this utility server to see data flow tree generated from privado.json.
If all works well you should see following message on your terminal.

```
privado json passed is : <repo folder location>/.privado/privado.json
Serving HTTP on :: port 8888 (http://[::]:8888/) ...
```

Open browser and hit URL `http://localhost:8888/`. It should open a page showing data flow tree generated from privado.json
